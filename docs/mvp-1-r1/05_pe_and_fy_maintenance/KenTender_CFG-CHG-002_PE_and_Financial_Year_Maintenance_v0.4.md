# CFG-CHG-002 — Procuring Entity and Financial Year Maintenance

**KenTender | Canonical Requirements and Design Specification**

| Item | Value |
|---|---|
| Change unit | CFG-CHG-002 |
| Module | Configuration and Governance |
| Version | 0.4 — Simplified Reference Data authority and lifecycle |
| Date | 27 August 2026 |
| Status | Proposed for approval |
| Scope | Procuring Entity, Financial Year and declared PE/FY context maintenance |
| Implementation posture | Greenfield reference-data control; Vue 3 inside Frappe Desk |
| Primary implementation owner | `kentender_core`, using native Frappe Roles and User Permissions |

## 1. Governing decision

KenTender shall maintain three distinct governed references:

1. a **Procuring Entity (PE)** is the enduring legal and operational identity of an entity using KenTender;
2. a **Financial Year (FY)** is the shared public-sector calendar period; and
3. a **PE/FY Context** is the explicit declaration that a named PE may operate in a named FY.

The PE/FY Context is a production reference record. It is not a saved selector value, a Planning Cycle, a dashboard filter or a seed-only combination.

An active PE/FY Context permits downstream modules to evaluate whether work may occur in that combination. It does not itself open a Departmental Needs window, create a Budget, create a Procurement Plan or authorize a user. Module configuration, native Frappe Role and User Permission scope, record state and server-side permission checks remain independently required.

Reference Data maintenance shall use one business role: **Reference Data Manager**. PE, FY and PE/FY Context maintenance shall not require a separate steward, central approver, PE configuration steward, professional configuration reviewer or Accounting Officer decision.

The safety controls are authoritative records, validation, effective dating, immutability after use, reasoned lifecycle actions, audit and fail-closed downstream resolution. This change unit does not impose a maker-checker chain where no documented legal or policy control requires one.

## 1.1 Narrow conflict disposition

| Existing statement | Disposition established by CFG-CHG-002 |
|---|---|
| CFG-CHG-001 states that a PE/FY combination is a seed-manifest context and not a production business entity. | Superseded only on this point. `PEFiscalYearContext` is a governed production reference required by Planning and other PE/FY-scoped modules. |
| CFG-CHG-001 states that Financial Years remain shared calendar records and must not be extended with module fields. | Retained. FY contains calendar facts only; module windows and workflow fields remain outside it. |
| PLN-GF-002 requires an active declared PE/FY context and prohibits Cartesian generation. | Retained and made maintainable by this change unit. |
| A context selector filters authority and never grants it. | Retained without qualification. |
| CFG-CHG-002 v0.3 defined five dedicated Reference Data actors and two approval chains. | Superseded. One Reference Data Manager performs the finite maintenance actions; existing business roles retain their transaction responsibilities outside Reference Data. |
| AUTH-ADR-001 v1.0 removed the custom capability store but retained the v0.3 role examples. | Corrected by AUTH-ADR-001 v1.1 and this change unit. No `reference_data.*` capability string or custom assignment is part of Reference Data authority. |

## 2. Purpose and outcomes

CFG-CHG-002 shall provide:

- one controlled register of Procuring Entities;
- one controlled register of Financial Years;
- explicit enablement and lifecycle control of valid PE/FY combinations;
- a common service for resolving the contexts an actor may lawfully view or use;
- durable historical identity for Strategy, Budget, Needs, Planning, Tendering and audit records;
- exact administrative screens for creating, activating, suspending and closing these references; and
- deterministic seed and acceptance contracts.

## 2.1 Scope exclusions

This change unit does not:

- create or approve a Strategy, Budget, Departmental Need, Procurement Plan, Requisition or Tender;
- define Needs-intake, departmental-plan, budget or tender windows;
- maintain organisation units, user accounts, assignments or delegations;
- add module-specific fields to a Financial Year;
- create a universal administrator override;
- generate every possible PE/FY combination;
- make a selected PE/FY context an authority grant; or
- migrate, alias or dual-write legacy masters.

## 3. Fixed external constraints

Only the following external constraints affect this change unit:

| ID | Constraint |
|---|---|
| CFG-PEFY-EC-001 | The MVP Financial Year runs from 1 July through 30 June. |
| CFG-PEFY-EC-002 | The MVP operational timezone is `Africa/Nairobi`. |
| CFG-PEFY-EC-003 | Procuring Entity classifications come from the governed PE Type catalogue; users do not enter free-text types. |

Source citations are retained only in the source register. They do not replace a field rule, state rule, permission rule or acceptance case.

## 4. Ownership and domain boundary

| Record or concern | Owner | Rule |
|---|---|---|
| Procuring Entity and active descriptive version | Configuration and Governance / `kentender_core` | Shared reference; other modules may read but not write it. |
| PE type catalogue | Configuration and Governance | Controlled reference used to resolve applicable routes. |
| Financial Year | Configuration and Governance / `kentender_core` | Shared immutable calendar reference after availability. |
| PE/FY Context | Configuration and Governance / `kentender_core` | Explicit valid combination; unique per PE and FY. |
| Reference-data actions and audit | Frappe audit plus immutable lifecycle entries | Record who acted, when, why and what changed; no second approval ledger. |
| Roles and scope | Native Frappe Role and User Permission records | Resolved at request and command time; not copied into PE/FY records. |
| Module windows and workflow | Owning business module through governed configuration | Reference the PE/FY Context; never extend the FY master. |
| Planning Cycle, Budget, Strategy and other transactions | Respective business module | Reference the context; never maintain a shadow PE/FY master. |

Cross-app consumers shall use public read and resolution services. They shall not deep-import implementation classes or update PE, FY or context records directly.

## 5. Canonical domain model

### 5.1 ProcuringEntity

Stable identity record.

| Field | Requirement |
|---|---|
| `pe_id` | Immutable generated identifier, for example `PE-MOH`. |
| `pe_code` | Required immutable uppercase code; unique after normalized comparison. |
| `current_version_id` | Active descriptive version currently in effect. |
| `record_status` | `DRAFT`, `ACTIVE`, `SUSPENDED` or `RETIRED`. |
| `effective_from` | Date from which the PE may be used. |
| `effective_to` | Optional terminal date; must be later than `effective_from`. |
| `created_by/at` | Immutable audit metadata. |

No PE record may be physically deleted after activation or reference by another record.

### 5.2 ProcuringEntityVersion

Governed descriptive and classification version.

| Field | Requirement |
|---|---|
| `version_id` / `version_no` | Immutable identity and ascending version number per PE. |
| `legal_name` | Required official name. |
| `display_name` | Required user-facing name; may equal legal name. |
| `pe_type_code` | Required active PE type reference. |
| `timezone` | Required IANA timezone; MVP fixture value is `Africa/Nairobi`. |
| `change_reason` | Required for every version after the initial draft. |
| `version_state` | `DRAFT`, `ACTIVE`, `SUPERSEDED` or `WITHDRAWN`. |
| `valid_from/to` | Non-overlapping effective interval for active versions. |

The PE code and stable PE identity are never changed through a version. A mistaken activated identity requires a governed retirement and a new PE record; business logic does not alias the two identities.

### 5.3 FinancialYear

Shared calendar record.

| Field | Requirement |
|---|---|
| `financial_year_id` | Immutable generated identifier, for example `FY-2027-2028`. |
| `start_year` | Required four-digit year. |
| `label` | Generated display label, for example `2027/28`. |
| `start_date` | Generated as 1 July of `start_year`. |
| `end_date` | Generated as 30 June of `start_year + 1`. |
| `timezone` | `Africa/Nairobi` for the MVP. |
| `record_status` | `DRAFT`, `AVAILABLE` or `RETIRED`. |
| `created_by/at`, `made_available_by/at` | Immutable audit metadata. |

`UPCOMING`, `CURRENT` and `PAST` are derived calendar phases, not editable statuses. No `is_current` field is permitted.

An FY is editable only in `DRAFT`. After it becomes `AVAILABLE`, its identifier, label and dates are immutable. A referenced FY cannot be deleted or repurposed.

Non-standard financial-year dates are outside MVP scope and require an approved change unit; users cannot override the generated dates in the UI.

### 5.4 PEFiscalYearContext

Stable declaration of one permitted PE/FY combination.

| Field | Requirement |
|---|---|
| `context_id` | Immutable generated identifier, for example `CTX-MOH-2027-2028`. |
| `pe_id` | Required reference to an active PE. |
| `financial_year_id` | Required reference to an available FY. |
| `context_status` | `SCHEDULED`, `ACTIVE`, `SUSPENDED` or `CLOSED`. |
| `active_from` | Required instant when the combination becomes available; it may precede the FY start to allow advance planning. |
| `active_to` | Required instant later than `active_from`; it may extend beyond FY end for governed close-out. |
| `closed_by/at/reason` | Required when manually closed. |
| `suspended_by/at/reason` | Required when suspended. |
| `expected_version` | Concurrency token for commands. |

Database uniqueness shall enforce one stable context per `(pe_id, financial_year_id)`. The platform shall never generate a Cartesian product of PEs and FYs.

More than one context may be active for the same PE. This supports current-year work, historical close-out and preparation of the next FY. Calendar phase, native user scope and module windows determine what work is actually available.

## 6. Lifecycle and governance

### 6.1 Procuring Entity lifecycle

| Source | Action | Result | Minimum authority and guard |
|---|---|---|---|
| — | Create draft | `DRAFT` | Reference Data Manager. Code is unique. |
| `DRAFT` | Activate | PE `ACTIVE`; version `ACTIVE` | Reference Data Manager; required fields complete. |
| `ACTIVE` | Propose amendment | New version `DRAFT` | Reference Data Manager; active version remains authoritative. |
| Amendment `DRAFT` | Apply amendment | Successor version `ACTIVE`; prior version `SUPERSEDED` | Reference Data Manager; reason required and stable identity unchanged. |
| `ACTIVE` | Suspend | `SUSPENDED` | Reference Data Manager; mandatory reason and impact warning. |
| `SUSPENDED` | Reinstate | `ACTIVE` | Reference Data Manager; reason and prerequisite revalidation. |
| `ACTIVE` or `SUSPENDED` | Retire | `RETIRED` | Effective date and reason required; no active/scheduled context may remain. |

Suspension or retirement blocks new PE/FY contexts and new business roots. It never deletes, hides or rewrites existing records.

### 6.2 Financial Year lifecycle

| Source | Action | Result | Minimum authority and guard |
|---|---|---|---|
| — | Create from start year | `DRAFT` | Reference Data Manager; derived identifier and dates are unique. |
| `DRAFT` | Make available | `AVAILABLE` | Reference Data Manager; generated identifier, label and dates are internally consistent. |
| `AVAILABLE` | Retire | `RETIRED` | Only when not used by an active/scheduled context; retirement does not remove history. |

FY availability is not the opening of a business process. No transaction is created when an FY becomes available.

### 6.3 PE/FY Context lifecycle

| Source | Action | Result | Authority and consequence |
|---|---|---|---|
| — | Enable PE for Financial Year | `ACTIVE` or `SCHEDULED` | Reference Data Manager; active PE, available FY, unique pair and valid availability dates required. |
| `SCHEDULED` | Reach `active_from` | `ACTIVE` | Automated activation after prerequisite revalidation. |
| `ACTIVE` | Suspend | `SUSPENDED` | Reference Data Manager; reason required. |
| `SUSPENDED` | Reinstate | `ACTIVE` or `SCHEDULED` | Reference Data Manager; reason and prerequisite revalidation. |
| `ACTIVE`/`SUSPENDED`/`SCHEDULED` | Close | `CLOSED` | Reference Data Manager; impact acknowledgement and reason required. |
| `ACTIVE` | Reach `active_to` | `CLOSED` | Automated closure with scheduler audit; existing records remain governed by their owning modules. |
| `CLOSED` | Reopen | `ACTIVE` or `SCHEDULED` | Reference Data Manager; reason, new availability dates and prerequisite revalidation required. |

A future context remains `SCHEDULED` until `active_from`.

Closing a context prevents new business roots and removes it from new-work selectors. It does not automatically cancel or invalidate existing Strategy, Budget, Needs, Plan, Tender or Contract records. Each owning module determines the lawful completion, correction or read-only treatment of existing work.

Enabling a PE/FY Context is an administrative reference-data action. It is not described as a statutory approval of the financial year or a substitute for downstream business approvals.

## 7. Roles and permissions

| Actor | PE | FY | PE/FY Context |
|---|---|---|---|
| Reference Data Manager | Create, activate, amend, suspend, reinstate and retire | Create, make available and retire | Enable, suspend, reinstate, close and reopen |
| Module consumer | Read minimum display fields | Read | Resolve only contexts permitted by native Frappe Role, User Permission and module rules |
| Internal Auditor | Read within oversight scope | Read | Read lifecycle history and audit; no maintenance action |
| System Manager | Administer users, Roles and User Permissions; assign Reference Data Manager where authorised | Same | Audited technical support; does not obtain downstream business approval authority |

Reference Data Manager is a global central Frappe Role for this finite register. It requires no PE-specific grant and no `reference_data.*` capability string. Assigning or revoking it uses standard Frappe administration and audit.

Head of Procurement Function and Accounting Officer retain their business roles in the modules that require their decisions. Those roles confer no Reference Data maintenance action.

The server shall resolve the actor's native Frappe Role, DocType permission and current record state at command time. Downstream context use additionally requires the exact native User Permission scope and owning-module rules.

## 8. Business rules

| ID | Invariant | Enforcement point |
|---|---|---|
| CFG-PEFY-BR-001 | Normalized PE code, FY identifier and Context identifier are unique. | Database constraint and command service. |
| CFG-PEFY-BR-002 | An `ACTIVE` PE has exactly one `ACTIVE` descriptive version, one active PE Type and one valid IANA timezone. | PE activation command. |
| CFG-PEFY-BR-003 | FY identifier, label, start date and end date are generated from `start_year` and cannot diverge. | FY creation command and database validation. |
| CFG-PEFY-BR-004 | An `AVAILABLE` FY may exist with zero PE/FY Contexts. | No automatic context creation. |
| CFG-PEFY-BR-005 | A Context can be enabled only for an `ACTIVE` PE and an `AVAILABLE` FY. | Context enable command. |
| CFG-PEFY-BR-006 | `active_to` is later than `active_from`; these dates do not define a module submission window. | Context enable and lifecycle commands. |
| CFG-PEFY-BR-007 | More than one Context may be `ACTIVE` for the same PE; no mutable global current-context flag exists. | Data model and resolver. |
| CFG-PEFY-BR-008 | Calendar phase is derived from the request date and never grants access or causes automatic selection. | FY projection and context resolver. |
| CFG-PEFY-BR-009 | A remembered Context is revalidated against current state, native User Permission scope and module eligibility on every read and command. | Context resolver and downstream command guard. |
| CFG-PEFY-BR-010 | List, count and selector results use the same server-side scope predicate. | Query services. |
| CFG-PEFY-BR-011 | Context activation creates no Strategy, Budget, Need, Planning Cycle, Plan or Tender. | Context activation transaction. |
| CFG-PEFY-BR-012 | New downstream work requires an `ACTIVE` Context plus the owning module's prerequisites. | Downstream command guard. |
| CFG-PEFY-BR-013 | Suspending or closing a Context does not mutate an existing downstream record. | Context transition transaction. |
| CFG-PEFY-BR-014 | An active master is not edited in place; a material change uses a successor version or an explicit state command. | Write services. |
| CFG-PEFY-BR-015 | A referenced PE, FY or Context is never physically deleted. | Delete guard and database policy. |
| CFG-PEFY-BR-016 | Every state command requires the current `expected_version`; a stale command has no partial effect. | Command service transaction. |
| CFG-PEFY-BR-017 | Every retriable state command uses an idempotency key and returns the original committed result on replay. | Command journal. |
| CFG-PEFY-BR-018 | Date-only values remain dates; instants are stored in UTC and displayed in the Context timezone. | Persistence and projection layers. |

## 9. Downstream context resolution

The common resolver shall accept the authenticated actor, requesting module/command, request time and optional remembered context. It shall:

1. resolve the actor's applicable Frappe Roles, native User Permissions and valid delegation where the owning module permits delegation;
2. join the native scope only to declared, active PE/FY Contexts;
3. apply exact PE/FY Context and optional Organisation Unit scope;
4. return zero, one or many authorized contexts;
5. revalidate a remembered selection and discard it if no longer authorized;
6. expose no record-existence signal outside authorized scope; and
7. return stable display data and context identifiers for downstream use.

Zero contexts produces an actionable no-access state. One context may be selected automatically. Multiple contexts require explicit user selection.

The resolver result shall include `context_id`, PE code/name/type snapshot, FY label/start/end, timezone, context status, actor visibility mode and available module actions. It shall never return an authority inferred from the selected context.

## 10. Service contracts

| Contract | Input | Output | Required control |
|---|---|---|---|
| `ListProcuringEntities` | Filters and page cursor | Authorized PE register projection | Server scope; stable pagination; no broad client filtering. |
| `GetProcuringEntity` | `pe_id` | Current version, lifecycle history and available actions | Revalidate read scope. |
| `CreateOrRevisePE` | Identity, classification, timezone and expected version | Draft projection | Reference Data Manager; unique code. |
| `ApplyPEAction` | PE/version, action, reason, expected version, idempotency key | Authoritative post-action projection | Reference Data Manager; state, dependency and audit checks. |
| `ListFinancialYears` | Filters | FY register with derived calendar phase | Central/reference read policy. |
| `CreateFinancialYear` | `start_year` | Generated Draft FY | No manual date override; uniqueness. |
| `MakeFinancialYearAvailable` | FY, expected version, idempotency key | Available FY | Reference Data Manager; immutable calendar. |
| `ListPEFYContexts` | Authorized filters | Context register and readiness diagnostics | Same scope predicate for counts and rows. |
| `EnablePEFYContext` | PE, FY, availability dates and idempotency key | Active or Scheduled projection | Reference Data Manager; unique pair and PE/FY prerequisites. |
| `ApplyPEFYContextAction` | Context, action, reason, dates, expected version, idempotency key | Authoritative projection | Reference Data Manager; state, dependency and audit checks. |
| `ResolveAuthorizedContexts` | Requesting module/command, request time, remembered context | Zero/one/many permitted contexts | Native Roles and User Permissions; deny by default. |
| `ValidateContextForCommand` | Actor, required Role, context, record, request time | Allow/deny plus safe reason code | Used by every downstream state-changing command. |

All state-changing services shall return the refreshed record state, server-computed available actions and new concurrency token.

## 11. UI architecture and routes

The production UI is one Vue 3 SFC application mounted in a standard Frappe Desk Page. It uses the existing Frappe build pipeline, shared KenTender shell/registries, vendor-neutral `--kt-*` tokens and Vue scoped styles. Claude Design runtime files are design evidence only and are never imported.

| Route | Purpose |
|---|---|
| `/app/reference-data/procuring-entities` | PE register tab. |
| `/app/reference-data/procuring-entities/{pe_id}` | PE detail, history and governed actions. |
| `/app/reference-data/financial-years` | FY register tab. |
| `/app/reference-data/financial-years/{financial_year_id}` | FY detail and governed actions. |
| `/app/reference-data/pe-fy-contexts` | Declared context register tab. |
| `/app/reference-data/pe-fy-contexts/{context_id}` | Context detail, readiness, lifecycle history and actions. |

The route segment is durable and refresh-safe. The selected tab and record are read from `frappe.get_route()`; no durable identity is kept only in `frappe.route_options`.

## 12. Static Claude Design contract

This section alone is supplied to Claude Design. It contains visual composition and fixed fixture data only. No other section is a design prompt.

### 12.1 Closed-input rules

- Produce the artboards listed in this section as static desktop screens at 1440 × 1024 px.
- Each artboard states its fixture actor, timestamp and Frappe header breadcrumb. These are fixture data outside the designed page canvas and are not rendered in the artboard.
- Design the page content area only. Do not redraw the Frappe Desk top bar, side navigation, existing Frappe header/breadcrumb component or browser chrome.
- Use the approved KenTender component library and design tokens already supplied with the project.
- Use every visible label, value, count, row, status, date, person, filename and button exactly as written below.
- Do not add sample data, charts, summary text, fields, rows, columns, actions, menus, icons, tooltips, dialogs or alternate states.
- Do not replace an exact value with a placeholder, generated name, lorem ipsum or inferred content.
- Do not describe or encode permissions, validation, workflow transitions, API calls, routes, event handling, loading logic or other behaviour.
- Do not render requirement IDs, fixture notes or implementation guidance in the artboards.

### 12.2 CFG-PEFY-DES-01 — Procuring Entities register

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data**

**Page content header**

- Title: **Reference data**
- Description: **Maintain Procuring Entities, Financial Years and PE/FY Contexts used across KenTender.**
- Right-aligned primary button: **New procuring entity**

**Tabs**

- **Procuring Entities 3** — selected
- **Financial Years 1**
- **PE/FY Contexts 3**

**Summary cards, left to right**

| Label | Value |
|---|---:|
| Active procuring entities | 3 |
| Available financial years | 1 |
| Active PE/FY contexts | 3 |
| Configuration required | 2 |

**Filter row, left to right**

- Search field containing no value; placeholder **Search code or name**
- Select showing **All PE types**
- Select showing **All statuses**

**Table**

| Code | Procuring entity | PE type | Status | Effective from | Action |
|---|---|---|---|---|---|
| PE-MOH | Ministry of Health | National Government Ministry | Active | 1 Jul 2026 | View |
| PE-NSSF | National Social Security Fund | State Corporation | Active | 1 Jul 2026 | View |
| PE-CGK | County Government of Kisumu | County Government | Active | 1 Jul 2026 | View |

Footer text: **Showing 1–3 of 3**

### 12.3 CFG-PEFY-DES-02 — Financial Years register

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data**

**Page content header**

- Title: **Reference data**
- Description: **Maintain Procuring Entities, Financial Years and PE/FY Contexts used across KenTender.**
- Right-aligned primary button: **New financial year**

**Summary cards, left to right**

| Label | Value |
|---|---:|
| Active procuring entities | 3 |
| Available financial years | 1 |
| Active PE/FY contexts | 3 |
| Configuration required | 2 |

**Tabs**

- **Procuring Entities 3**
- **Financial Years 1** — selected
- **PE/FY Contexts 3**

**Filter row, left to right**

- Search field containing no value; placeholder **Search financial year**
- Select showing **All calendar phases**
- Select showing **All reference statuses**

**Table**

| Financial year | Period | Calendar phase | Reference status | PE/FY contexts | Action |
|---|---|---|---|---:|---|
| 2027/28 | 1 Jul 2027–30 Jun 2028 | Upcoming | Available | 3 | View |

Footer text: **Showing 1 of 1**

### 12.4 CFG-PEFY-DES-03 — PE/FY Contexts register

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data**

**Page content header**

- Title: **Reference data**
- Description: **Maintain Procuring Entities, Financial Years and PE/FY Contexts used across KenTender.**
- Right-aligned primary button: **Enable PE for financial year**

**Summary cards, left to right**

| Label | Value |
|---|---:|
| Active procuring entities | 3 |
| Available financial years | 1 |
| Active PE/FY contexts | 3 |
| Configuration required | 2 |

**Tabs**

- **Procuring Entities 3**
- **Financial Years 1**
- **PE/FY Contexts 3** — selected

**Filter row, left to right**

- Search field containing no value; placeholder **Search context or procuring entity**
- Select showing **All procuring entities**
- Select showing **All financial years**
- Select showing **All statuses**

**Table**

| Context | Procuring entity | Financial year | Available from–to | Status | Readiness | Action |
|---|---|---|---|---|---|---|
| CTX-MOH-2027-2028 | Ministry of Health | 2027/28 | 1 Jan 2027, 00:00 EAT–30 Sep 2028, 23:59 EAT | Active | Configuration required | View |
| CTX-NSSF-2027-2028 | National Social Security Fund | 2027/28 | 1 Jan 2027, 00:00 EAT–30 Sep 2028, 23:59 EAT | Active | Ready | View |
| CTX-CGK-2027-2028 | County Government of Kisumu | 2027/28 | 1 Jan 2027, 00:00 EAT–30 Sep 2028, 23:59 EAT | Active | Configuration required | View |

Footer text: **Showing 1–3 of 3**

### 12.5 CFG-PEFY-DES-04 — Active Procuring Entity detail

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > Procuring Entities > PE-MOH**

**Page content header**

- Title: **PE-MOH — Ministry of Health**
- Status: **Active**
- Right-aligned secondary button: **Propose amendment**

**Identity card**

| Label | Value |
|---|---|
| PE code | PE-MOH |
| Legal name | Ministry of Health |
| Display name | Ministry of Health |
| PE type | National Government Ministry |
| Effective from | 1 Jul 2026 |

**Operational setting card**

| Label | Value |
|---|---|
| Timezone | Africa/Nairobi |

**History card**

| Date and time | Event | Actor |
|---|---|---|
| 30 Jun 2026, 16:25 EAT | Activated | Lydia Mwangi |
| 29 Jun 2026, 10:10 EAT | Draft created | Lydia Mwangi |

### 12.6 CFG-PEFY-DES-05 — New Financial Year draft

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > Financial Years > New financial year**

**Page content header**

- Title: **New financial year**
- Status: **Draft**

**Financial year card**

| Field label | Displayed value |
|---|---|
| Start year | 2028 |
| Financial year | 2028/29 |
| Start date | 1 Jul 2028 |
| End date | 30 Jun 2029 |
| Timezone | Africa/Nairobi |

Start year uses the approved text-input component. Financial year, Start date, End date and Timezone use the approved read-only field component.

**Fixed footer, left to right:** **Cancel**, **Save draft**, **Make available**. **Make available** is the primary button.

### 12.7 CFG-PEFY-DES-06 — Active PE/FY Context detail

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > PE/FY Contexts > CTX-MOH-2027-2028**

**Page content header**

- Title: **PE-MOH | FY 2027/28**
- Description: **Declared PE/FY Context for Ministry of Health.**
- Status: **Active**
- Right-aligned secondary button: **Suspend**
- Right-aligned danger-outline button: **Close context**

**Context card**

| Label | Value |
|---|---|
| Context ID | CTX-MOH-2027-2028 |
| Procuring Entity | PE-MOH — Ministry of Health |
| Financial Year | FY-2027-2028 — 2027/28 |
| Active from | 1 Jan 2027, 00:00 EAT |
| Active to | 30 Sep 2028, 23:59 EAT |

**Core readiness card**

| Check | Result |
|---|---|
| Procuring Entity active | Ready |
| Financial Year available | Ready |
| PE type configured | Ready |
| Timezone configured | Ready |

**Module readiness card**

| Module | Result |
|---|---|
| Strategy Alignment | Ready |
| Budget Configuration | Ready |
| Departmental Needs | Configuration required |
| Procurement Planning | Configuration required |

**Lifecycle history card**

| Date and time | Event | Actor |
|---|---|---|
| 1 Jan 2027, 00:00 EAT | Context activated | System |
| 15 Dec 2026, 14:40 EAT | Enabled for FY 2027/28 | Lydia Mwangi |

### 12.8 CFG-PEFY-DES-07 — Close Context dialog

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > PE/FY Contexts > CTX-MOH-2027-2028**

Duplicate the completed CFG-PEFY-DES-06 artboard without changing its content or layout. Dim that duplicate and place the following dialog over it.

| Element | Exact content |
|---|---|
| Dialog title | Close PE/FY context |
| Context summary | PE-MOH — Ministry of Health · FY 2027/28 |
| Consequence text | This context will no longer appear in new-work selectors. Existing records will remain available according to their module rules. |
| Reason label | Closure reason |
| Reason value | 2027/28 initiation period completed; retain context for historical work only. |
| Checkbox label | I understand that this removes the context from new-work selectors but does not cancel existing records. |
| Checkbox state | Checked |
| Secondary button | Cancel |
| Danger primary button | Close context |

### 12.9 CFG-PEFY-DES-08 — Register state variants

Create four static variants. Every variant contains exactly this page content header and tab row:

- Title: **Reference data**
- Description: **Maintain Procuring Entities, Financial Years and PE/FY Contexts used across KenTender.**
- No header action button
- Tabs: **Procuring Entities 3**, **Financial Years 1**, **PE/FY Contexts 3**
- Selected tab: **PE/FY Contexts 3**

The standard filter row contains an empty search field with placeholder **Search context or procuring entity**, a select showing **All procuring entities**, a select showing **All financial years**, and a select showing **All statuses**. Do not show summary cards or data rows in these variants.

Fixture context for Loading, No matches and Server error — outside the artboard: **Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT**. Fixture context for Forbidden — outside the artboard: **Grace Wanjiku · Departmental Need Requester · 15 Mar 2027, 11:30 EAT**. Frappe header breadcrumb for all four variants: **Home > Configuration and Governance > Reference data**.

| Variant | Filter row | Main content | Buttons |
|---|---|---|---|
| Loading | Standard filter row with all four controls disabled | Five full-width skeleton table rows | None |
| No matches | Search value **Ministry of Education**; selects show **All procuring entities**, **All financial years** and **All statuses** | Heading **No records match these filters.** Body **Change or clear the filters to see other PE/FY contexts.** | **Clear filters** |
| Forbidden | No filter row | Heading **You do not have access to maintain reference data.** Body **Ask your KenTender administrator to assign the Reference Data Manager role.** | None |
| Server error | Standard filter row | Heading **Reference data could not be loaded.** Body **Try again. If the problem continues, contact KenTender support.** | **Try again** |

### 12.10 CFG-PEFY-DES-09 — New Procuring Entity draft

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > Procuring Entities > New procuring entity**

**Page content header**

- Title: **New procuring entity**
- Status: **Draft**

**Identity card**

| Field label | Displayed value |
|---|---|
| PE code | PE-KEMSA |
| Legal name | Kenya Medical Supplies Authority |
| Display name | Kenya Medical Supplies Authority |
| PE type | State Corporation |
| Effective from | 1 Jul 2027 |

**Operational setting card**

| Field label | Displayed value |
|---|---|
| Timezone | Africa/Nairobi |

**Fixed footer, left to right:** **Cancel**, **Save draft**, **Activate procuring entity**. **Activate procuring entity** is the primary button.

Do not show a generated internal record ID, contact fields, source-reference fields, attachments, decision history, change reason, PE/FY Contexts, module configuration, approval stepper or destructive action.

### 12.11 CFG-PEFY-DES-10 — Available Financial Year detail

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > Financial Years > FY-2027-2028**

**Page content header**

- Title: **Financial year 2027/28**
- Status: **Available**
- No header action button

**Calendar card**

| Label | Value |
|---|---|
| Financial Year ID | FY-2027-2028 |
| Start year | 2027 |
| Start date | 1 Jul 2027 |
| End date | 30 Jun 2028 |
| Timezone | Africa/Nairobi |
| Calendar phase | Upcoming |

**Declared PE/FY Contexts card**

| Context | Procuring entity | Status | Action |
|---|---|---|---|
| CTX-MOH-2027-2028 | Ministry of Health | Active | View |
| CTX-NSSF-2027-2028 | National Social Security Fund | Active | View |
| CTX-CGK-2027-2028 | County Government of Kisumu | Active | View |

Footer text inside the Contexts card: **3 declared contexts**

Do not show editable calendar fields, an **Open financial year** action, a **Close financial year** action, a **Set current** action, module windows, transaction totals or an approval stepper.

### 12.12 CFG-PEFY-DES-11 — Enable PE for Financial Year

**Fixture context — outside the artboard:** Lydia Mwangi · Reference Data Manager · 15 Mar 2027, 11:30 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > Reference data > PE/FY Contexts > Enable PE for financial year**

**Page content header**

- Title: **Enable PE for financial year**
- Description: **Declare when a Procuring Entity and Financial Year combination is available to KenTender modules.**

**Context card**

| Field label | Displayed state |
|---|---|
| Context ID | Not assigned |
| Procuring Entity | Empty select; placeholder **Select procuring entity** |
| Financial Year | Empty select; placeholder **Select financial year** |
| Active from | Empty date-time field; placeholder **DD MMM YYYY, HH:MM** |
| Active to | Empty date-time field; placeholder **DD MMM YYYY, HH:MM** |
| Timezone | Africa/Nairobi |

**Core readiness card**

| Check | Result |
|---|---|
| Procuring Entity active | Not assessed |
| Financial Year available | Not assessed |
| PE type configured | Not assessed |
| Timezone configured | Not assessed |

**Fixed footer, left to right:** **Cancel**, **Enable context**. **Enable context** is visibly disabled until the required values pass validation.

Do not show reason fields, source-reference fields, attachments, Module readiness, governance history, approval actions, module windows, Strategy records, Budget records, Needs records, Procurement Plan records or an approval stepper.

### 12.13 Existing downstream PE/FY selector

No new selector artboard is authorised by this change unit. Reuse the previously approved KenTender PE/FY workspace control without visual modification. Do not ask Claude Design to produce a replacement selector, selector menu, context-switch dialog or module workspace.

## 13. Functional interaction requirements — excluded from design prompts

This section defines runtime behaviour and system rules. It is for requirements, implementation and testing. It must not be copied into Claude Design.

### 13.1 CFG-PEFY-UI-01 — Reference data workspace

**Breadcrumb:** Home > Configuration and Governance > Reference data

**Title:** Reference data

**Description:** Maintain Procuring Entities, Financial Years and the PE/FY contexts used across KenTender.

Persistent tabs:

- **Procuring Entities**
- **Financial Years**
- **PE/FY Contexts**

The active tab is represented by the URL. Browser back/forward restores the prior tab and record without remounting a second Vue application.

The page does not show the normal downstream PE/FY workspace selector. Maintenance access requires the Reference Data Manager Frappe Role.

#### Procuring Entities tab

Toolbar, left to right:

- Search placeholder: **Search code or name**
- **PE type** filter
- **Status** filter
- primary button: **New procuring entity** when authorized

Table columns:

| Code | Procuring entity | PE type | Status | Effective from | Action |
|---|---|---|---|---|---|

Row action is **Continue draft** or **View** as returned by the server. There is no inline editing.

#### Financial Years tab

Toolbar:

- Search placeholder: **Search financial year**
- **Reference status** filter
- **Calendar phase** filter
- primary button: **New financial year** when authorized

Table columns:

| Financial year | Period | Calendar phase | Reference status | PE/FY contexts | Action |
|---|---|---|---|---|---|

#### PE/FY Contexts tab

Toolbar:

- Search placeholder: **Search context or procuring entity**
- **Procuring entity** filter
- **Financial year** filter
- **Status** filter
- primary button: **Enable PE for financial year** when authorized

Table columns:

| Context | Procuring entity | Financial year | Available from–to | Status | Readiness | Action |
|---|---|---|---|---|---|---|

**Readiness** shows **Ready** or **Configuration required**. It is computed, not editable. Selecting **Configuration required** opens the context detail at the readiness panel.

Common states:

- Loading: skeleton rows; filters disabled; no false zero count.
- Empty register: **No records match these filters.** with **Clear filters**.
- No records exist: contextual message and create action only when authorized.
- Forbidden: **You do not have access to maintain reference data.** No counts or record names are disclosed.
- Server failure: inline error panel with **Try again**; existing content is not silently cleared.

### 13.2 CFG-PEFY-UI-02 — Procuring Entity detail

**Title:** `{PE code} — {display name}` or **New procuring entity**

**Header status:** server status badge

**Header actions:** exactly the server-computed next actions.

Sections:

1. **Identity** — PE code, legal name, display name.
2. **Classification** — PE type and effective dates.
3. **Operational setting** — timezone.
4. **Change reason** — displayed for amendments.
5. **Lifecycle history** — read-only version and action timeline.

Draft footer: **Cancel | Save draft | Activate procuring entity**. Amendment drafts use **Apply amendment** instead of **Activate procuring entity**.

An active record has no **Edit** action. The action is **Propose amendment**, which creates a new Draft version while the active version remains displayed as the current authority.

**Suspend** opens a dialog titled **Suspend procuring entity** with consequence text: **New PE/FY contexts and new business records will be blocked. Existing records will remain available according to their module rules.** A 20–500 character reason is required.

**Retire** is disabled while an active or scheduled context exists. The disabled explanation names the number of blocking contexts without exposing unauthorized records.

### 13.3 CFG-PEFY-UI-03 — Financial Year detail

**Title:** `{label}` or **New financial year**.

New FY form:

| Field | Interaction |
|---|---|
| Start year | Four-digit integer. |
| Financial year | Generated read-only label. |
| Start date | Generated read-only 1 July date. |
| End date | Generated read-only 30 June date. |
| Timezone | Read-only `Africa/Nairobi` for MVP. |

Footer: **Cancel | Save draft | Make available**.

Changing the start year immediately regenerates the identifier preview, label and dates. If an FY for that start year already exists, the field shows **Financial year {label} already exists** and **Make available** remains disabled.

Once available, calendar fields are read-only. The screen shows derived calendar phase and linked PE/FY Context count. No action named **Open financial year**, **Close financial year** or **Set current** is shown.

### 13.4 CFG-PEFY-UI-04 — PE/FY Context detail

**Title:** `{PE code} | FY {label}` or **Enable PE for financial year**

**Description:** Declare when this Procuring Entity and Financial Year combination is available to KenTender modules.

**Status:** server status badge.

Sections:

1. **Context** — Procuring Entity, Financial Year and generated Context ID.
2. **Availability** — Active from, Active to and timezone display.
3. **Core readiness** — PE active, FY available, PE type configured, timezone configured.
4. **Module readiness** — read-only diagnostics such as Strategy, Budget, Needs and Planning prerequisites. Missing module configuration does not rewrite core context status.
5. **Lifecycle history** — enablement, scheduled activation, activation, suspension, closure and reopening actions.

When PE and FY are selected, the client requests a server-generated context ID and duplicate check. Client validation never replaces the database uniqueness constraint.

**Enable context** opens a summary dialog showing PE, FY, availability dates and the statement: **Enabling this context permits scheduled availability of this PE/FY combination. It does not create or approve any Strategy, Budget, Need or Procurement Plan.** Actions: **Cancel | Enable context**.

**Suspend** requires a reason and shows affected new-work modules.

**Close context** requires a reason and the confirmation checkbox **I understand that this removes the context from new-work selectors but does not cancel existing records.**

**Reopen** requires a reason, new availability dates and prerequisite revalidation.

After every successful command, the UI replaces its local projection with the server response, updates available actions and shows one success notification. It does not optimistically invent the resulting workflow state.

### 13.5 Downstream PE/FY selector

The shared downstream selector shall:

- show only server-resolved contexts authorized for the current module through native Roles and User Permissions;
- display **{PE short name} | FY {label}**;
- show no selector when zero contexts are authorized;
- auto-select the sole authorized context;
- require selection when more than one is authorized;
- revalidate a remembered context on page load, refresh and command;
- preserve selection in a durable route or shared state whose authority is revalidated;
- warn before switching when the current screen has unsaved changes; and
- state: **This selection changes the workspace view. It does not grant access or change record ownership.**

A closed or suspended context is excluded from new-work selectors. Authorized historical views may offer it through a separately labelled **Historical contexts** control.

## 14. Error contract

| Code | User message |
|---|---|
| `PE_CODE_DUPLICATE` | A Procuring Entity with this code already exists. |
| `PE_NOT_ACTIVE` | This Procuring Entity is not active. |
| `FY_ALREADY_EXISTS` | This Financial Year already exists. |
| `FY_NOT_AVAILABLE` | This Financial Year is not available for use. |
| `PEFY_CONTEXT_DUPLICATE` | This PE/FY context already exists. |
| `PEFY_DATES_INVALID` | The context availability end must be later than its start. |
| `PEFY_PREREQUISITE_MISSING` | Complete the listed core configuration before enabling this context. |
| `PEFY_CONTEXT_NOT_ACTIVE` | This PE/FY context is not available for new work. |
| `AUTHORITY_REQUIRED` | You are not authorized to perform this action. |
| `VERSION_CONFLICT` | This record changed after you opened it. Refresh and review the latest version. |
| `REFERENCE_IN_USE` | This reference cannot be retired while the listed active dependencies remain. |

Unauthorized errors shall not disclose whether an out-of-scope PE, FY or context exists.

## 15. Audit and historical integrity

Every create, activate, make-available, enable, amend, suspend, reinstate, close, reopen, retire and denied command shall record:

- actor and applicable Frappe Role;
- target record and version;
- PE/FY scope;
- command and outcome;
- UTC timestamp and display timezone;
- expected and resulting version;
- mandatory reason where applicable;
- request/idempotency identifier; and
- before/after content hashes for material changes.

Downstream transactions retain stable `pe_id`, `financial_year_id` and `context_id` references plus appropriate display snapshots. Later master-data changes never rewrite historical transaction evidence.

## 16. Seed contract

The MVP seed shall create exactly these reference records and declared combinations:

| Identifier | Record | Value |
|---|---|---|
| `PE-MOH` | Procuring Entity | Ministry of Health — Active |
| `PE-NSSF` | Procuring Entity | National Social Security Fund — Active |
| `PE-CGK` | Procuring Entity | County Government of Kisumu — Active |
| `FY-2027-2028` | Financial Year | 1 July 2027–30 June 2028; Africa/Nairobi — Available |
| `CTX-MOH-2027-2028` | PE/FY Context | MOH + FY 2027/28 — Active |
| `CTX-NSSF-2027-2028` | PE/FY Context | NSSF + FY 2027/28 — Active |
| `CTX-CGK-2027-2028` | PE/FY Context | CGK + FY 2027/28 — Active |

The seeded PE versions shall contain these exact values:

| PE | PE type | Effective from | Timezone |
|---|---|---|---|
| PE-MOH | National Government Ministry | 1 Jul 2026 | Africa/Nairobi |
| PE-NSSF | State Corporation | 1 Jul 2026 | Africa/Nairobi |
| PE-CGK | County Government | 1 Jul 2026 | Africa/Nairobi |

All three seeded Contexts shall use **1 Jan 2027, 00:00 EAT** as `active_from` and **30 Sep 2028, 23:59 EAT** as `active_to`.

The design and test fixture shall expose these exact readiness results at **15 Mar 2027, 11:30 EAT**:

| Context | Strategy Alignment | Budget Configuration | Departmental Needs | Procurement Planning | Overall display |
|---|---|---|---|---|---|
| CTX-MOH-2027-2028 | Ready | Ready | Configuration required | Configuration required | Configuration required |
| CTX-NSSF-2027-2028 | Ready | Ready | Ready | Ready | Ready |
| CTX-CGK-2027-2028 | Ready | Configuration required | Configuration required | Configuration required | Configuration required |

The fixture actors are:

| User | Display name | Assignment |
|---|---|---|
| lydia.mwangi@kentender.example.test | Lydia Mwangi | Reference Data Manager |
| grace.wanjiku@moh.example.test | Grace Wanjiku | Departmental Need Requester — PE-MOH |

The seeded history shall contain these exact committed events:

| Record | Date and time | Event | Actor |
|---|---|---|---|
| PE-MOH | 29 Jun 2026, 10:10 EAT | Draft created | Lydia Mwangi |
| PE-MOH | 30 Jun 2026, 16:25 EAT | Activated | Lydia Mwangi |
| CTX-MOH-2027-2028 | 15 Dec 2026, 14:40 EAT | Enabled for FY 2027/28 | Lydia Mwangi |
| CTX-MOH-2027-2028 | 1 Jan 2027, 00:00 EAT | Context activated | System |

The **New procuring entity** artboard uses unsaved `PE-KEMSA` data, and the **New financial year** artboard uses an unsaved design fixture for start year **2028**. Neither is an additional production seed record.

Seeds are deterministic and idempotent. Running them twice creates no duplicate master, version, lifecycle entry, context or audit record. Seeds shall fail on conflicting authoritative data and shall not repair, alias or import legacy records.

## 17. Acceptance contract

| ID | Scenario | Expected result |
|---|---|---|
| CFG-PEFY-AC-001 | Reference Data Manager creates a PE with a unique valid code and complete required fields. | Draft is saved; no active PE is created. |
| CFG-PEFY-AC-002 | Duplicate normalized PE code is submitted. | `PE_CODE_DUPLICATE`; no partial record. |
| CFG-PEFY-AC-003 | Reference Data Manager activates a complete PE Draft. | PE and initial version become Active; action is audited. |
| CFG-PEFY-AC-004 | Active PE is amended. | Successor Draft is created; active version remains authoritative until successor activation. |
| CFG-PEFY-AC-005 | PE with active contexts is retired. | Blocked with dependency explanation; no state change. |
| CFG-PEFY-AC-006 | FY start year 2027 is entered. | `FY-2027-2028`, label `2027/28`, 1 July 2027 and 30 June 2028 are generated. |
| CFG-PEFY-AC-007 | User attempts to edit dates of an available FY. | UI is read-only and direct API command is rejected. |
| CFG-PEFY-AC-008 | FY is made available. | No PE/FY Context or downstream transaction is automatically created. |
| CFG-PEFY-AC-009 | Context is enabled for inactive PE or unavailable FY. | Enablement is blocked with safe prerequisite errors. |
| CFG-PEFY-AC-010 | Duplicate PE/FY pair is created concurrently. | Database uniqueness allows one stable context only; retry resolves to the existing result where idempotent. |
| CFG-PEFY-AC-011 | Future context is enabled. | It remains Scheduled and activates only at `active_from` after revalidation. |
| CFG-PEFY-AC-012 | Current and next FY contexts are active for one PE. | Both may exist; authorized selector returns them according to native Role, User Permission and module rules. |
| CFG-PEFY-AC-013 | Actor selects a context outside their native User Permission scope. | Server denies without disclosing out-of-scope data. |
| CFG-PEFY-AC-014 | Remembered context is suspended after page load. | Next read/command revalidation removes or rejects it and refreshes the UI. |
| CFG-PEFY-AC-015 | Context is closed. | It disappears from new-work selectors; existing downstream records remain unchanged. |
| CFG-PEFY-AC-016 | Reference Data Manager reopens a closed context with new valid dates and a reason. | Context becomes Active or Scheduled after revalidation; action is audited. |
| CFG-PEFY-AC-017 | Stale expected version submits a lifecycle action. | `VERSION_CONFLICT`; no partial effects. |
| CFG-PEFY-AC-018 | Same activation command is retried with the same idempotency key. | Original successful result is returned without a second lifecycle entry. |
| CFG-PEFY-AC-019 | System Administrator selects support context. | Read-only labelled support projection; no business actions. |
| CFG-PEFY-AC-020 | Workspace loads through entry link, direct URL, refresh and browser back/forward. | Correct tab/record and shell render without duplicate Vue mount, console error or lost route identity. |
| CFG-PEFY-AC-021 | Seed runs twice. | No duplicate PE, FY, context, version or lifecycle records. |
| CFG-PEFY-AC-022 | Downstream module requests all configured contexts client-side. | No such broad API exists; server returns only contexts permitted through native Role, User Permission and module rules. |
| CFG-PEFY-AC-023 | A design artboard in Section 12 is compared with its fixture table. | Every visible label, value, row, count, status and button matches; no additional visible content exists. |
| CFG-PEFY-AC-024 | Section 12 is supplied to Claude Design without any other section. | Every specified artboard can be produced without inventing or requesting data; the downstream selector is explicitly retained rather than redesigned. |
| CFG-PEFY-AC-025 | The Section 12 prompt text is inspected. | It contains no positive instruction for permission, validation, workflow, API, routing, event handling or state transition; those subjects appear only in the closed-input prohibition. |

### 17.1 Minimum rule coverage

| Requirement | Acceptance coverage |
|---|---|
| CFG-PEFY-EC-001–003 | CFG-PEFY-AC-001, 006, 007 and 009 |
| CFG-PEFY-BR-001–003 | CFG-PEFY-AC-002, 006, 007, 010 and 021 |
| CFG-PEFY-BR-004–006 | CFG-PEFY-AC-008, 009 and 011 |
| CFG-PEFY-BR-007–010 | CFG-PEFY-AC-012, 013, 014 and 022 |
| CFG-PEFY-BR-011–015 | CFG-PEFY-AC-004, 005, 008, 015 and 016 |
| CFG-PEFY-BR-016–018 | CFG-PEFY-AC-017 and 018 |
| UI architecture and static design contract | CFG-PEFY-AC-020 and 023–025 |

## 18. Implementation and test constraints

- Use standard Frappe DocTypes, document services, permission APIs, transactions and audit facilities.
- Use one Reference Data Manager Frappe Role. Do not implement the five v0.3 roles or any `reference_data.*` capability string.
- Business transitions reside in Python services; Vue renders server projections and invokes explicit commands.
- Use one Vue application per Frappe page wrapper and do not remount on every page show.
- Use scoped component CSS and canonical `--kt-*` tokens. Do not import Claude Design runtime, Tailwind CDN or global generated CSS.
- Register the route in the shared shell and applicable UI registries.
- Apply database uniqueness to PE code, FY start year/identifier and PE/FY pair.
- All commands enforce authority, state, expected version and idempotency server-side.
- Test focused service rules first, then API permission/transition contracts, Vue component states and targeted Playwright journeys.
- Do not run the full KenTender suite after each local correction; run the CFG-CHG-002 gate after a coherent slice and broader contracts at cutover.

## 19. Prohibited shortcuts

- An editable global **Current financial year** flag.
- A selector populated with every PE and FY.
- Automatic generation of all PE/FY combinations.
- Treating an active context as a user authority grant.
- Storing module windows, budget status or plan state on Financial Year.
- Editing an active PE version or available FY in place.
- Deleting referenced PE, FY or context records.
- Treating System Manager or Administrator technical access as a downstream procurement approval.
- Creating downstream records when an FY or context is activated.
- Client-only permission, lifecycle or duplicate checks.
- Permanent parallel legacy and Vue maintenance screens.

## 20. Traceability sources

| Source | Use |
|---|---|
| CFG-CHG-001 — Configuration and Governance Foundation v0.2 | Control-plane, versioning and audit principles retained where consistent with this simplification. |
| PLN-GF-002 — Plan Cycle and PE/FY Governance v0.2 | Declared-context requirement, context resolution, fixtures and downstream Planning boundary. |
| Public Finance Management Act, 2012 | Financial-year and public-finance control context: <https://new.kenyalaw.org/akn/ke/act/2012/18/eng@2024-04-26> |
| Public Procurement and Asset Disposal Act, 2015 | PE accountability, structured decision-making and annual planning: <https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31> |
| Public Procurement and Asset Disposal Regulations, 2020 | PE/FY planning and approval-process context: <https://new.kenyalaw.org/akn/ke/act/ln/2020/69/eng@2022-12-31> |

---

**Approval effect.** Approval of CFG-CHG-002 v0.4 makes `ProcuringEntity`, `FinancialYear` and `PEFiscalYearContext` the canonical shared references for new KenTender implementation and establishes Reference Data Manager as their only maintenance Role. It does not by itself authorize repository changes, data migration, role cutover or unrelated configuration or transactional functionality.
