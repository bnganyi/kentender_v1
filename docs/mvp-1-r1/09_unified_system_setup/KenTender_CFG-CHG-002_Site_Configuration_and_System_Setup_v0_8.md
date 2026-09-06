# CFG-CHG-002 — Site Configuration and System Setup

| Control | Value |
|---|---|
| Document ID | CFG-CHG-002 |
| Version | 0.8 |
| Date | 2 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Module | Configuration and Governance |
| Change type | Complete successor to v0.7. Implements LAW-REG-001 v1.0 items C1–C3 from the primary text of the Act and Regulations, including the Second and Third Schedules. Earlier change: Adds the departmental-plan intake flag, the statutory approval route, the funding-source catalogue and the effective-dated regulator reference register. |
| Standards | Governed by KT-STD-001 v1.1. Sections not restated here are inherited from it. |
| Implementation owner | `kentender_core`, using ERPNext and Frappe records where they already exist |

**Controlling decision:** One KenTender site is one Procuring Entity, configured once at first run and never selected afterwards. Fiscal years are ERPNext `Fiscal Year` records. Departmental-needs intake is a flag on the applicable Fiscal Year. All site configuration is maintained by Administrator or System Manager on one page, `/app/system-setup`, taking effect on save with no approval workflow.

---

## 1. Governing decision

This document owns four things:

1. the **site Procuring Entity** record and its first-run creation;
2. the **Fiscal Year** surface over ERPNext, including namespaced module intake flags;
3. the **Organisation Unit** records, whose scope semantics are defined by AUTH-ADR-001; and
4. the **System setup** page shell that hosts every configuration section, including the two owned by AUTH-ADR-001.

It replaces CFG-CHG-002 v0.1–v0.5 and withdraws CTX-CHG-001 in full.

The fiscal-year intake flag in §4.2 is a **pattern**, not a one-off. Planning, Budget and other modules will each need one. This document is where that pattern accretes, so that adding a module flag never requires reopening an architecture decision record.

### 1.1 Conflict and disposition register

| Earlier item | Disposition in v0.6 |
|---|---|
| A register of many Procuring Entities | Remove. One site is one PE. The register, its filters, its create flow and `ListProcuringEntities` are deleted. |
| `ProcuringEntity` as an ordinary DocType | Replace with a Frappe **Single**, so singularity is structural rather than enforced by a validation a fixture can bypass. |
| `ProcuringEntityVersion` and the draft-activate-supersede chain | Remove. A Single has no register to protect from in-place edits. Changes are audited field edits; legal provenance on issued documents is a name-and-code snapshot under AUTH-ADR-001 v1.6 §4.1. |
| PE lifecycle states `DRAFT`, `ACTIVE`, `SUSPENDED`, `RETIRED` | Remove. Suspending the entity that owns the site has no meaning. |
| `PEFiscalYearContext`, its lifecycle, register, readiness diagnostics and resolver | Remove entirely. A PE/FY combination is not a record when there is one PE. |
| `ResolveAuthorizedContexts` and `ValidateContextForCommand` | Remove. Authorization is AUTH-ADR-001's resolver, registered as Frappe permission hooks. |
| Downstream PE/FY selector | Remove. A Fiscal Year control in a module screen is a local, changeable filter only. |
| KenTender-owned `FinancialYear` DocType | Replace with ERPNext `Fiscal Year`, extended by namespaced custom fields only. |
| `Reference Data Manager` role | Remove. Administrator and System Manager maintain configuration directly under AUTH-ADR-001 v1.6 §8. No business role, approval chain or `reference_data.*` capability string exists. |
| `/app/reference-data/*` routes and their three tabbed registers | Replace with `/app/system-setup`. No alias or redirect after cutover. |
| Summary cards counting PEs, FYs and contexts | Remove. |
| PE Type catalogue as a governed reference resolving applicable routes | Reduce to one descriptive field. Nothing branches on it in this release. |
| KenTender-owned unit catalogue | Replace with ERPNext `UOM`. |
| Needs intake as a scheduled window record | Remain removed. Replaced by a flag with one optional close instant — a field, not a lifecycle. |
| Needs-submission flag as a bare boolean | Correct. Add optional `closes_at`, because NDS-CHG-001 v1.4 §11.2 already displays **Open until 25 Nov 2026, 23:59 EAT** while its domain model carries only a boolean. |
| v0.5's restatement of the design closed-input rules, verification protocol, release evidence and universal prohibitions | Remove. Cite KT-STD-001 v1.1. |

---

## 2. Purpose and exclusions

**Outcomes:** one configured site identity available without a selection step; one canonical fiscal-year catalogue shared with ERPNext accounting; one audited control over whether departmental-needs intake is open and for which year; and one page on which an administrator completes the whole setup journey.

**This document does not:** define business authority or scope resolution (AUTH-ADR-001); define Departmental Needs behaviour (NDS-CHG-001); define budget, planning or tender windows; introduce any approval stage for a configuration write; or support more than one Procuring Entity in any form.

The non-goals in AUTH-ADR-001 v1.6 §2.2 — cross-PE supplier identity, national reporting and PPRA oversight — apply here unchanged.

---

## 3. Constraints and ownership

| ID | Constraint |
|---|---|
| CFG-EC-001 | The Kenyan public-sector fiscal year runs 1 July through 30 June. Non-standard dates are outside MVP scope. |
| CFG-EC-002 | The operational timezone is `Africa/Nairobi`. Instants are stored UTC and displayed in the site timezone. |
| CFG-EC-003 | ERPNext is installed on the same site for accounting and payroll. Its `Fiscal Year`, `Company` and `UOM` records are shared, not duplicated. |

| Record or concern | Owner |
|---|---|
| Site Procuring Entity, including the statutory approval route; System setup shell, tabs and routing | This document |
| ERPNext `Fiscal Year` and its namespaced module flags | ERPNext, governed here |
| `Organisation Unit` records | This document |
| Organisation Unit scope semantics, descendant rule, role registry, assignments, permission hooks | AUTH-ADR-001 |
| Units of measure | ERPNext `UOM`, curated at seed |
| Funding sources | This document — small governed catalogue, read-only to every module |
| Regulator reference register: threshold matrix, reservation categories and targets, market price index | This document, effective-dated. Owned here, interpreted by the consuming module |
| ERPNext `Company`, Cost Center, HRMS `Department` | ERPNext / HRMS. None is a KenTender scope dimension. |
| Module windows, states and workflow | Each business module |

Cross-app consumers use the services in §7. They do not deep-import implementation classes or write configuration records directly.

---

## 4. Canonical domain model

### 4.1 Site Procuring Entity — Single DocType

| Field | Rule |
|---|---|
| `pe_name` | Required. Official legal name. 2–200 characters. |
| `pe_code` | Required uppercase stable code, 3–20 characters. Set once at first run, read-only thereafter. |
| `pe_type` | Required select: `National Government Ministry`, `State Department`, `State Corporation`, `County Government`, `County Corporation`, `Constitutional Commission`, `Public University`, `Other Public Entity`. Descriptive only. |
| `ppra_registration` | Optional regulator reference. |
| `timezone` | Required IANA timezone. `Africa/Nairobi` by default. |
| `statutory_approval_route` | Required select with **four** values: `Cabinet Secretary`, `County Executive Committee Member`, `Board of Directors` or `Council`. The signature block of the Third Schedule to the Regulations reads "Approved by: Cabinet Secretary / CECM / Board / Council", and regulation 40(4) requires the consolidated annual procurement plan to be approved above the accounting officer. There is no `None` value; exactly one route applies to every entity. `Council` covers entities governed by a council rather than a board, such as a public university. |
| `entity_is_county` | Check. Set where the entity is a county government entity. Regulation 40(5) then requires the plan to indicate a minimum 20% allocation for resident tenderers of the county, and regulation 151 makes counties, sub-counties and constituencies the regions for exclusive preference. |
| `configured_by` / `configured_at` | Server-set at first save. |

- `pe_code` is immutable after first save. A mistaken code requires a new site, not an alias.
- Other fields are editable; the framework Version record captures every change.
- Because a Single cannot be the target of a `Link`, no transactional record carries a live PE foreign key. Immutable legal evidence stamps `pe_name` and `pe_code` as a snapshot at issue, so a later rename never rewrites a historical notice, award or contract.
- Creating a second Procuring Entity is structurally impossible.

### 4.2 Fiscal Year — ERPNext `Fiscal Year` with namespaced extensions

KenTender uses the ERPNext DocType unchanged and adds only:

| Custom field | Rule |
|---|---|
| `kentender_needs_submission_open` | Check, default 0. At most one Fiscal Year may have this enabled at any instant. |
| `kentender_needs_submission_closes_at` | Optional datetime. Valid only while the flag is enabled; must be in the future when set. Reaching it closes intake automatically. |
| `kentender_flag_changed_by` / `kentender_flag_changed_at` | Server-set on every change to either field above. |

Generation rules:

- `year_start_date` is 1 July of the chosen start year; `year_end_date` is 30 June of the following year. Neither is user-entered.
- `year` follows the ERPNext convention `2027-2028`. KenTender displays `FY 2027/28`, derived from `year_start_date`. No display label is stored.
- The site Company is added to the `companies` child table on creation, so ERPNext accounting recognises the year.
- `Upcoming`, `Current` and `Past` are derived from the request date. No `is_current` field is permitted.
- A year is disabled through ERPNext's own `disabled` field, and only when unreferenced with every intake flag off.

**Asset disposal plan intake.** The disposal plan is annual under section 53(4) and regulation 176, so it takes the same pattern:

| Custom field | Rule |
|---|---|
| `kentender_disposal_plan_open` | Check, default 0. At most one Fiscal Year may have it enabled. |
| `kentender_disposal_plan_closes_at` | Optional datetime. Reaching it closes intake automatically. |

**Departmental plan intake.** The same pattern governs Procurement Planning's departmental plan intake, replacing the `DPPSubmissionWindow` DocType removed by PLN-CHG-001 v1.8 §4.1:

| Custom field | Rule |
|---|---|
| `kentender_dpp_submission_open` | Check, default 0. At most one Fiscal Year may have it enabled. |
| `kentender_dpp_submission_closes_at` | Optional datetime. Reaching it closes intake automatically. Regulation 40(3) requires a departmental plan before the financial year commences, so this is normally set at or before 30 June preceding the plan year. |

Each module flag is independent: needs intake and departmental-plan intake may be open for different Fiscal Years at the same time, which is the normal sequence.

**Flag pattern rule.** A future module flag follows the same shape: a `kentender_{module}_{purpose}` check, an optional `_closes_at` datetime, and the two audit fields. It is added here, not in the consuming module's document. A flag never carries workflow state, a status enum or a window lifecycle.

### 4.3 Organisation Unit

Field rules, the single-root rule, the descendant rule and the absence of a `procuring_entity` field are defined in AUTH-ADR-001 v1.6 §4.2–4.3 and are not restated.

This document owns only:

- creation of the root Organisation Unit idempotently, in the same transaction as the first save of the site Procuring Entity, named `pe_name` and coded `pe_code`;
- generation of unit codes on insert as `OU-{pe_code_suffix}-{sequence}`, immutable thereafter; and
- a governed repair command that recreates a missing root without disturbing existing units.

### 4.4 Funding sources

Budget & Funding requires a governed funding-source catalogue that v0.6 left without an owner. It is a small KenTender DocType, not an ERPNext record, because no ERPNext catalogue carries the same meaning.

| Field | Rule |
|---|---|
| `funding_source_name` | Required. For example `Government of Kenya`, `Development partner`, `Appropriation in Aid`. |
| `enabled` | Check. Modules read only enabled records. |

Maintained in System setup. Referenced by Procurement Budget Lines and carried into downstream funding snapshots.

### 4.4A Regulator reference register

Three PPRA-published references change independently of this codebase, on gazette or quarterly cycles. They are **effective-dated**: every record carries the Fiscal Year or date range it applies to, superseded versions are retained, and consumers resolve the version in force for the record they are working on — never the current one. A plan approved under a 2027 gazette must remain auditable against that gazette.

| Register | Content | Consumer |
|---|---|---|
| **Threshold matrix** | The Second Schedule matrix, keyed on **goods, works and services** separately because the limits differ. Low value procurement: KES 50,000 goods, 100,000 works, 50,000 services, **per item per financial year**. Request for quotations: KES 3,000,000 goods, 5,000,000 works, 3,000,000 services, per request. Restricted tender under section 102(1)(b): KES 30,000,000 goods, 30,000,000 works, 20,000,000 services. Open tender, request for proposals and the other restricted limbs: no minimum, maximum determined by the funds allocated for the particular procurement. Direct procurement: no minimum or maximum subject to the section 103 conditions. | Procurement Planning, blocking |
| **Exclusive preference thresholds** | Regulation 163: KES 1,000,000,000 for works, construction materials and other materials made in Kenya; KES 500,000,000 for goods and services. | Procurement Planning, derived classification |
| **Reservation categories and targets** | The section 157(4) classes — disadvantaged groups, micro small and medium enterprises, works services and goods, identified regions — the 30% target under regulation 149 and section 53(6), and the county resident-tenderer minimum of 20% under regulation 40(5) and section 33(2)(g). The regions are counties, sub-counties and constituencies under regulation 151. | Procurement Planning, advisory |
| **Margins of preference** | Regulation 164: 20%, 15%, 10%, 8% and 6% of evaluated price by Kenyan shareholding and origin of goods. Applies at tender evaluation, not planning; held here so Tender Management inherits it rather than rediscovering it. | Tender Management |
| **Market price index** | Standard goods, works and services with known market prices, published quarterly by the Authority under section 54(3) and regulation 43(2). | Procurement Planning, display only |

Configuration & Governance owns the records and their effective dating. It does not interpret them: a module decides what blocks and what advises. No module writes to this register.

A missing threshold matrix for a Fiscal Year is a configuration defect that fails the consuming check closed. A missing reservation target or price index degrades to "not published" and blocks nothing.

### 4.5 Units of measure

Units come from ERPNext `UOM`. KenTender defines no unit DocType, no `other_unit` free-text field and no parallel catalogue. The enabled set is curated by seed and maintained through the standard ERPNext UOM list, to which the Fiscal years tab provides a labelled link. Modules read only records where `enabled = 1`.

---

## 5. Lifecycle and business rules

### 5.1 Lifecycle

| Object | Action | Result |
|---|---|---|
| Site with no PE | Configure procuring entity | PE saved; root Organisation Unit created in the same transaction. |
| PE configured | Edit descriptive fields | Fields updated; `pe_code` unchanged; Version records the change. |
| — | Add fiscal year from start year | Enabled Fiscal Year with generated dates and the site Company attached. |
| Fiscal year | Open needs submission | Flag enabled here and, atomically, disabled on any other year. Optional close instant recorded. |
| Intake open | Close needs submission | Flag disabled. Audited with actor, instant and reason. |
| Intake open with close instant | Reach the instant | Flag disabled by the scheduler, audited with `System` as actor. |
| Fiscal year, unreferenced, flags off | Disable | ERPNext `disabled` set. History retained. |

There is no draft, activation, suspension, retirement or approval state anywhere in this document. Opening or closing intake creates no Departmental Need, Plan, Budget or task, and is not a statutory approval of the year.

Only one Fiscal Year may have needs intake open at a time. Opening a second is one atomic command that closes the first, never two independent writes. This supports advance planning: FY 2027/28 intake may be open while accounting continues in FY 2026/27.

Organisation Unit add, rename, deactivate and reactivate are defined in AUTH-ADR-001 v1.6 §14.1. Reparent and physical delete are not implemented.

### 5.2 Business rules

| ID | Invariant | Enforcement point |
|---|---|---|
| CFG-BR-001 | Exactly one Procuring Entity exists per site. | Single DocType. |
| CFG-BR-002 | `pe_code` is immutable after first save. | Save validation. |
| CFG-BR-003 | First save of the PE creates the root Organisation Unit in the same transaction. | Configure command. |
| CFG-BR-004 | Fiscal Year dates are generated from the start year and cannot be overridden. | Add-fiscal-year command. |
| CFG-BR-005 | Fiscal Year identifiers are unique. | Database constraint and command. |
| CFG-BR-006 | At most one Fiscal Year has `kentender_needs_submission_open` enabled at any instant. | Atomic open command **and** a database-level partial unique index or equivalent guard. A read-then-write check alone is insufficient. |
| CFG-BR-007 | A close instant, when set, is in the future and belongs to the year whose flag is open. | Open command, validated against the server clock. |
| CFG-BR-008 | Reaching the close instant disables the flag and writes an audited entry with `System` as actor. | Hourly scheduled job. |
| CFG-BR-009 | Opening or closing intake creates no downstream record. | Command transaction. |
| CFG-BR-010 | A Fiscal Year referenced by any KenTender record, or with an intake flag on, cannot be disabled. | Disable guard. |
| CFG-BR-011 | Adding a Fiscal Year attaches the site Company. | Add-fiscal-year command. |
| CFG-BR-012 | No configuration write enters a draft, submission, review or approval state. | Command services and DocType definitions. |
| CFG-BR-013 | At most one Fiscal Year has `kentender_dpp_submission_open` enabled at any instant, enforced by the same guard as CFG-BR-006. Needs intake and departmental-plan intake are independent and may be open for different years. | Atomic open command and a database-level guard. |
| CFG-BR-014 | `statutory_approval_route` is required and has no `None` value. A site cannot be configured without one. | Save validation. |
| CFG-BR-015 | Every regulator reference record carries the Fiscal Year or date range it applies to. Superseded versions are retained and never edited in place. | Save validation and delete guard. |
| CFG-BR-016 | A regulator reference read resolves the version in force for the requested Fiscal Year, never the current date. | Read service. |

KT-STD-001 §11 supplies the concurrency, idempotency and stale-command rules applying to every command here.

---

## 6. Roles and permissions

| Actor | Permitted configuration work |
|---|---|
| Administrator | Configure the site PE; add and disable Fiscal Years; open and close needs submission; maintain Organisation Units; grant and revoke responsibilities under AUTH-ADR-001. |
| System Manager | The same, subject to standard Frappe role permissions. |
| Every other actor | No configuration write. Configuration values are read through the modules that display them. |

There is no Reference Data Manager, configuration steward, configuration reviewer or Accounting Officer decision.

Configuration authority is not business authority. Under AUTH-ADR-001 v1.6 §8, an Administrator who opens needs submission still cannot create, review or accept a Departmental Need without the applicable responsibility assignment.

---

## 7. Service and command contracts

| Contract | Input | Output | Required control |
|---|---|---|---|
| `GetSiteConfiguration()` | — | PE identity, timezone, root unit presence, open intake year and close instant | Cached per request; safe for any authenticated actor. |
| `ConfigureProcuringEntity(name, code, type, ppra_ref, timezone, idempotency_key)` | Identity fields | Saved PE plus created root unit | Administrator or System Manager; rejected if a PE exists. |
| `UpdateProcuringEntity(fields, expected_version)` | Editable fields only | Refreshed PE | `pe_code` rejected if present. |
| `ListFiscalYears(filters)` | Optional filters | Years with derived phase, intake state and KenTender reference counts | Server-side projection. |
| `AddFiscalYear(start_year, idempotency_key)` | Four-digit start year | Enabled Fiscal Year with generated dates and Company attached | Uniqueness; no date override. |
| `OpenNeedsSubmission(fiscal_year, closes_at, reason, expected_version, idempotency_key)` | Target year, optional close instant | Refreshed years | Atomically closes any other open year; audited. |
| `CloseNeedsSubmission(fiscal_year, reason, expected_version, idempotency_key)` | Target year | Refreshed year | Audited with reason. |
| `SetFiscalYearDisabled(fiscal_year, disabled, expected_version)` | Target year | Refreshed year | Blocked by references or an open flag, with exact blockers. |
| `RepairOrganisationRoot(idempotency_key)` | — | Created root unit | Administrator only; no effect if a root exists. |

Organisation Unit and responsibility commands are defined in AUTH-ADR-001 v1.6 §9.2.

---

## 8. Error contract

| Code | User-visible result |
|---|---|
| `CFG_PE_NOT_CONFIGURED` | This site has no Procuring Entity yet. Configure it before using KenTender. |
| `CFG_PE_ALREADY_CONFIGURED` | This site already has a Procuring Entity. |
| `CFG_PE_CODE_IMMUTABLE` | The Procuring Entity code cannot be changed after it is set. |
| `CFG_ROOT_UNIT_MISSING` | The root organisation unit is missing. Run the governed repair before assigning responsibilities. |
| `CFG_FY_ALREADY_EXISTS` | This financial year already exists. |
| `CFG_FY_IN_USE` | This financial year cannot be disabled while the listed records reference it. |
| `CFG_INTAKE_CLOSE_INSTANT_INVALID` | The closing time must be in the future. |
| `CFG_INTAKE_NOT_OPEN` | Needs submission is not open for this financial year. |
| `CFG_AUTHORITY_REQUIRED` | You are not authorised to change site configuration. |
| `CFG_VERSION_CONFLICT` | This record changed after you opened it. Refresh and review the latest version. |

Message conventions are in KT-STD-001 §11.

---

## 9. UI architecture, menu and routes

**System setup** is one Vue 3 page mounted in a standard Frappe Desk page, and the only entry under **Configuration and Governance**.

| Route | Purpose |
|---|---|
| `/app/system-setup` | Complete site configuration. Opens the first incomplete tab. |
| `#procuring-entity` | Site identity. |
| `#fiscal-years` | Fiscal years and needs-submission intake. |
| `#organisation-structure` | Organisation Unit tree. Content per AUTH-ADR-001 v1.6 §13.2–13.3. |
| `#users-and-responsibilities` | Responsibility register, assignment and revocation. Content per AUTH-ADR-001 v1.6 §13.4–13.9. |

A shared header is followed by four horizontal tabs, each rendering one section into the full content column. A hash anchor selects its tab; refresh, direct load and browser back and forward preserve it.

Raw `/app/procuring-entity`, `/app/fiscal-year`, `/app/organisation-unit`, `/app/user-responsibility-assignment`, `/app/user-permission` and every `/app/reference-data/*` route are removed from navigation with no alias or redirect.

---

## 10. Static Claude Design contract

Supply **KT-STD-001 §2 plus this section** to Claude Design. Nothing else. The closed-input rules, product-wide prohibitions, approved desktop shell and division of supply are in KT-STD-001 §2.2–2.5 and are not repeated here. The Organisation structure and Users and responsibilities tabs are supplied by AUTH-ADR-001 v1.6 §13 and are not redrawn here.

**Additional prohibitions for this document:** do not show a PE/FY context record, a readiness matrix, a context register, a count or summary card, an approval control, a submit control or a draft badge.

**Shared page header, used on every full-page artboard in this document and in AUTH-ADR-001 v1.6 §13:**

- Eyebrow: **CONFIGURATION AND GOVERNANCE**
- Title: **System setup**
- Description: **Configure this KenTender site, its financial years, organisational structure and user responsibilities.**
- No header action button

**Tab row, in this order:** **Procuring entity** · **Fiscal years** · **Organisation structure** · **Users and responsibilities**.

Fixture actors, organisation units, fiscal years and units of measure come from KT-STD-001 §8.

### 10.1 CFG-DES-01 — Procuring entity tab, configured

**Fixture context — outside the artboard:** Administrator · `administrator@moh.example.test` · 1 Sep 2026, 09:40 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**

Tab **Procuring entity** is selected.

**Identity card**

- Card heading: **Procuring entity**
- Card description: **This site represents one procuring entity. The code is fixed once the site is configured.**

| Field label | Displayed value | Component |
|---|---|---|
| Entity code | PE-MOH | Read-only field |
| Entity name | Ministry of Health | Single-line input |
| Entity type | National Government Ministry | Select |
| PPRA registration | PPRA/PE/2019/0114 | Single-line input |
| Timezone | Africa/Nairobi | Select |

**Configuration record card**

| Label | Value |
|---|---|
| Configured by | Administrator |
| Configured at | 29 Jun 2026, 10:10 EAT |
| Root organisation unit | Ministry of Health · PE-MOH |

**Sticky page footer:** right-aligned primary button **Save changes**.

Do not show a delete, suspend or retire control, a version history table, a PE list or an "add another entity" action.

### 10.2 CFG-DES-02 — First run, no procuring entity configured

**Fixture context — outside the artboard:** Administrator · `administrator@newsite.example.test` · 1 Sep 2026, 08:00 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**

The tab row is present with **Procuring entity** selected and the other three tabs disabled.

**Setup notice**

- Heading: **Configure this site**
- Text: **KenTender represents one procuring entity. Enter its details to create the site and its root organisation unit.**

**Identity card** — heading **Procuring entity**

| Field label | Displayed value | Component |
|---|---|---|
| Entity code | PE-MOH | Single-line input |
| Entity name | Ministry of Health | Single-line input |
| Entity type | National Government Ministry | Select |
| PPRA registration | Empty | Single-line input, placeholder **Optional** |
| Timezone | Africa/Nairobi | Select |

Help text beneath the code input: **The entity code cannot be changed after this site is configured.**

**Sticky page footer:** right-aligned primary button **Configure site**.

Do not show a Cancel action, a skip action, a progress stepper or a multi-step wizard.

### 10.3 CFG-DES-03 — Fiscal years tab

**Fixture context — outside the artboard:** Administrator · `administrator@moh.example.test` · 24 Nov 2026, 09:15 EAT · Frappe header breadcrumb: **Home > Configuration and Governance > System setup**

Tab **Fiscal years** is selected.

**Section intro**

- Heading: **Financial years**
- Description: **Financial years are shared with accounting. Needs submission may be open for one year at a time.**
- Right-aligned primary button: **Add financial year**

**Table**

| Financial year | Period | Phase | Needs submission | Action |
|---|---|---|---|---|
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | Current | Closed | Open needs submission |
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Upcoming | Open until 25 Nov 2026, 23:59 EAT | Close needs submission |

Below the table: **2 financial years** on the left. No pagination control.

The **Needs submission** cell for FY 2027/28 uses the approved active state badge; FY 2026/27 uses the approved neutral state badge.

**Units link** — below the table, a single text link **Manage units of measure** with the supporting line **Units are shared with accounting and maintained in the standard units list.**

### 10.4 CFG-DES-04 — Add financial year dialog

520 px modal over a dimmed CFG-DES-03. Title: **Add financial year**.

| Field label | Displayed value | Component |
|---|---|---|
| Start year | 2028 | Single-line numeric input |

Read-only summary panel beneath the input:

> FY 2028/29 · 1 Jul 2028 – 30 Jun 2029

Footer buttons: **Cancel** and primary **Add financial year**.

Do not show start-date or end-date inputs, a label input, a company selector or a needs-submission control.

### 10.5 CFG-DES-05 — Open needs submission dialog

520 px modal over a dimmed CFG-DES-03.

- Title: **Open needs submission**
- Text: **Departments will be able to create and submit needs for FY 2027/28.**

| Field label | Displayed value | Component |
|---|---|---|
| Close automatically on | 25 Nov 2026, 23:59 | Optional date and time input |
| Reason | Annual needs call issued under circular MOH/PROC/2026/07. | Multiline text area |

Help text beneath the close input: **Leave blank to keep submission open until you close it.**

**Replacement notice** — between the fields and the footer:

- Heading: **This will close FY 2026/27**
- Text: **Needs submission can be open for one financial year at a time. Submission for FY 2026/27 will close when you continue.**

Footer buttons: **Cancel** and primary **Open needs submission**.

### 10.6 CFG-DES-06 — Close needs submission dialog

520 px modal over a dimmed CFG-DES-03.

- Title: **Close needs submission?**
- Text: **Departments will no longer be able to create or submit needs for FY 2027/28. Needs already submitted or accepted are unaffected.**
- Field label: **Reason**
- Exact value: **Needs call closed on the date announced in circular MOH/PROC/2026/07.**
- Footer buttons: **Cancel** and destructive **Close needs submission**

### 10.7 CFG-DES-07 — Common states

Four variants using the shell and page header above. State treatments follow KT-STD-001 §3; the exact copy is:

| Variant | Exact visible content |
|---|---|
| Loading | Tab row with **Fiscal years** selected; table card with **Loading financial years…** and approved skeleton rows. |
| No financial years | Heading **No financial years yet**; text **Add the first financial year for this site.**; primary button **Add financial year**. |
| Forbidden | Heading **System setup is not available**; text **You do not have the technical access required to configure this site.**; no tabs, table or action. |
| Error | Heading **System setup could not be loaded**; text **Try again. If the problem continues, contact support.**; secondary button **Try again**. |

---

## 11. Functional interaction requirements — excluded from design prompts

Common page behaviour and accessibility follow KT-STD-001 §3 and are not restated.

### 11.1 Page shell and routing

- On load, `GetSiteConfiguration()` resolves in one call. With no PE, the page opens the Procuring entity tab, shows the setup notice and disables the other three tabs.
- With a PE but no root Organisation Unit, the Organisation structure tab shows the repair state in AUTH-ADR-001 v1.6 §13.9 and the Users and responsibilities tab is disabled.
- Otherwise the page opens the tab named by the hash anchor, or Procuring entity when none is given.
- Tab changes update the hash without a full route change.
- The page registers in `cl_surface_registry` and `STITCH_DESK_SURFACES`, provides `data-testid="back-to-workbench"` and returns to Configuration and Governance rather than raw `/desk`.

### 11.2 Procuring entity tab

- `Configure site` is available only when no PE exists. It validates code format, then creates the PE and root Organisation Unit in one transaction. On success the remaining tabs become available without a page reload.
- After configuration the code input becomes read-only. A direct API attempt returns `CFG_PE_CODE_IMMUTABLE`.
- `Save changes` is disabled until a field changes and re-disables after a successful save.
- Timezone changes take effect for display immediately. Stored instants are unchanged.

### 11.3 Fiscal years tab

- Rows are ordered by `year_start_date` descending. Phase is derived server-side from the request date.
- The dialog summary for a new year is computed by the server preview, not the client. Dates are never user-entered.
- The per-row action is `Open needs submission` when the flag is off and `Close needs submission` when on. No row offers both.
- The replacement notice appears only when another year currently has intake open, and names that exact year. The command closes the other and opens the target in one transaction.
- A close instant is revalidated against the server clock rather than the client clock.
- An hourly scheduled job closes any year whose close instant has passed, auditing `System` as actor. The job is a convenience, not a security control: every module command rechecks the flag server-side in its own transaction.
- Disabling a year is blocked while referenced or while an intake flag is on, returning exact blockers.
- `Manage units of measure` opens the standard ERPNext UOM list. KenTender renders no unit editor.

### 11.4 Organisation structure and Users and responsibilities tabs

Behaviour is defined in AUTH-ADR-001 v1.6 §14.1–14.4. This document supplies only the tab container, the selected-tab state and the shared header.

### 11.5 Configuration consumption by modules

- Modules read configuration through `GetSiteConfiguration()` or the equivalent server projection, never by querying the PE Single, the Fiscal Year custom fields or the Organisation Unit table directly.
- Intake flags are read-only to every module. No module exposes a command that changes one, and none renders an intake-window editor.
- A module command depending on a flag rechecks it server-side in the same transaction as its write.
- Closing intake never rewrites, deletes or hides an existing record. The consequences for existing drafts belong to the owning module.

---

## 12. Audit and historical integrity

Every configuration command records actor, target record, command, outcome, UTC instant, expected and resulting version, mandatory reason where applicable, idempotency identifier and before-and-after values for material changes.

- Site PE field changes are captured by the framework Version record. `pe_code` never changes.
- Every change to an intake flag or its close instant is audited, including automatic closure, which records `System` as actor.
- Configuration records are never physically deleted once referenced.
- Downstream records retain stable Fiscal Year and Organisation Unit references plus the PE name-and-code snapshot appropriate to their evidence type. Later configuration changes never rewrite historical transaction evidence.

---

## 13. Seed contract

Site configuration, Organisation Units, actors and fiscal years come from KT-STD-001 §8. Seed execution rules come from KT-STD-001 §8.6.

This document additionally seeds:

- **ERPNext Company** — Ministry of Health, corresponding to the site PE.
- **PPRA registration** — `PPRA/PE/2019/0114`.
- **Enabled `UOM` records** — `Each`, `Programme`, `Set`, `Lot`, `Kilogram`, `Litre`, `Metre`, `Square Metre`, `Cubic Metre`, `Service Month`. All others disabled.
- **Configuration history** — PE configured by Administrator at 29 Jun 2026, 10:10 EAT.

The FY 2027/28 intake state — open, closing 25 Nov 2026, 23:59 EAT — matches the fixture in NDS-CHG-001 v1.4 §11.2 at a fixture time of 24 Nov 2026, 15:00 EAT.

---

## 14. Acceptance contract

| ID | Required result |
|---|---|
| CFG-AC-001 | A new site with no configuration opens System setup on the Procuring entity tab with the other tabs disabled. |
| CFG-AC-002 | Configuring the entity creates the PE and its root Organisation Unit in one transaction; a failure leaves neither. |
| CFG-AC-003 | Creating a second Procuring Entity is impossible through the UI, the API and a fixture. |
| CFG-AC-004 | `pe_code` cannot be changed after first save, through the UI or a direct API call. |
| CFG-AC-005 | Renaming the entity does not alter the code, the root unit code or any previously issued document snapshot. |
| CFG-AC-006 | No PE selector, switcher, column or PE/FY context record appears anywhere in the product. |
| CFG-AC-007 | `PEFiscalYearContext`, the KenTender `FinancialYear` DocType and every `/app/reference-data/*` route are absent after cutover. |
| CFG-AC-008 | Adding a fiscal year from start year 2028 generates 1 Jul 2028 – 30 Jun 2029 and attaches the site Company. |
| CFG-AC-009 | Fiscal year dates cannot be overridden through the UI or a direct API call. |
| CFG-AC-010 | Adding an existing fiscal year is rejected without creating a partial record. |
| CFG-AC-011 | Opening needs submission for a second year closes the first in the same transaction; under concurrent open commands, at no observable instant are two years open. |
| CFG-AC-012 | A close instant in the past is rejected against the server clock, not the client clock. |
| CFG-AC-013 | Reaching the close instant disables the flag and writes an audited entry with `System` as actor. |
| CFG-AC-014 | A module command depending on the flag rechecks it server-side and is denied when the flag closed after page load. |
| CFG-AC-015 | Opening or closing needs submission creates no Departmental Need, Plan, Budget or task. |
| CFG-AC-016 | Disabling a referenced fiscal year is blocked with exact blockers and no state change. |
| CFG-AC-017 | FY 2027/28 intake can be open while FY 2026/27 remains the current accounting year. |
| CFG-AC-018 | No configuration write enters a draft, submission, review or approval state. |
| CFG-AC-019 | An Administrator who opens needs submission still cannot create, review or accept a Departmental Need without the applicable responsibility assignment. |
| CFG-AC-020 | No `Reference Data Manager` role, `reference_data.*` capability string or configuration approval chain exists. |
| CFG-AC-021 | Units come only from enabled ERPNext `UOM` records; no KenTender unit DocType or free-text unit field exists. |
| CFG-AC-022 | A missing root organisation unit shows the repair state, disables the responsibilities tab, and is fixed by the governed repair without disturbing existing units. |
| CFG-AC-023 | A stale `expected_version` returns `CFG_VERSION_CONFLICT` with no partial effect, and a retried command with the same idempotency key returns the original result without a second audit entry. |
| CFG-AC-024 | Direct route, hash anchor, refresh and browser back and forward restore the correct tab without a duplicate Vue mount or console error. |
| CFG-AC-025 | Loading, empty, forbidden and error states are visibly distinct and never appear as an empty successful table. |
| CFG-AC-026 | ERPNext accounting and HRMS payroll continue to function after cutover; their Fiscal Year, Company and UOM records are shared, not duplicated or replaced. |
| CFG-AC-027 | A new module intake flag can be added following §4.2 without changing an architecture decision record. |
| CFG-AC-029 | A second module intake flag can be added under §4.2 without changing an architecture decision record, and needs intake and departmental-plan intake can be open for different Fiscal Years simultaneously. |
| CFG-AC-030 | A site cannot be configured without a statutory approval route; four values are available — Cabinet Secretary, County Executive Committee Member, Board of Directors and Council — and no value permits skipping statutory approval. |
| CFG-AC-030a | The threshold register returns different limits for goods, works and services, and a consumer cannot resolve admissibility without supplying the category. |
| CFG-AC-030b | The county resident-tenderer control is available only where `entity_is_county` is set. |
| CFG-AC-030c | Needs intake, departmental plan intake and disposal plan intake are independent flags and may be open for different Fiscal Years simultaneously. |
| CFG-AC-031 | A regulator reference read for a past Fiscal Year returns the version in force then, not the current one, and a superseded version is retained unedited. |
| CFG-AC-032 | A missing threshold matrix for a requested Fiscal Year is reported as a configuration defect; a missing reservation target or price index reports "not published" without error. |
| CFG-AC-033 | Funding sources come only from the enabled governed catalogue, and Budget seeds resolve `Government of Kenya` from it. |
| CFG-AC-028 | Every artboard in §10 matches its fixture table exactly, and §10 supplied alone to Claude Design with KT-STD-001 §2 and §8 produces every artboard without inventing or requesting data. |

---

## 15. Implementation and test constraints

The implementation baseline is KT-STD-001 §4; the verification protocol is KT-STD-001 §5; release evidence is KT-STD-001 §6.

### 15.1 Additional implementation rules

- Implement the site PE as a Frappe Single DocType. Do not add a count validation to an ordinary DocType instead.
- Extend ERPNext `Fiscal Year` through Custom Fields shipped as fixtures under the `kentender_` prefix. Do not fork, override or duplicate the DocType.
- Enforce the single-open-year rule at the database level where the engine supports a partial unique index, and in the command transaction in every case.
- Implement automatic close as an hourly scheduled job. Every dependent command still rechecks the flag in its own transaction.

### 15.2 Additional minimum coverage

1. First-run configuration creating PE and root unit atomically, including rollback on failure.
2. Second-PE creation attempts through UI, API and fixture.
3. `pe_code` immutability through UI and direct API.
4. Fiscal year generation, uniqueness and Company attachment.
5. Date-override rejection through UI and direct API.
6. Single-open-year invariant under concurrent open commands.
7. Close instant validation against the server clock.
8. Scheduled automatic closure and its audit entry.
9. Server-side flag recheck when the flag closes between page load and command.
10. Fiscal year disable blocked by references and by an open flag.
11. Advance-planning case: FY 2027/28 intake open while FY 2026/27 is current.
12. Configuration authority without business authority.
13. Root-repair command with and without an existing root.
14. ERPNext and HRMS non-interference after cutover.
15. Repository scan proving `PEFiscalYearContext`, the KenTender `FinancialYear` DocType, `Reference Data Manager`, every `reference_data.*` string and every `/app/reference-data/*` route are absent.
16. Browser journey: configure a new site end to end — entity → fiscal year → open intake → assign a responsibility — on one route.

---

## 16. Prohibited shortcuts

The universal list is KT-STD-001 §2.3 and §10. Additionally, for this document:

- Do not reintroduce `PEFiscalYearContext`, a PE/FY combination record, a readiness matrix or a context resolver.
- Do not create a KenTender `FinancialYear` DocType, a year wrapper or a shadow year table.
- Do not add module workflow fields to `Fiscal Year` beyond the namespaced flag pattern in §4.2.
- Do not add an editable global **Current financial year** flag or an `is_current` field.
- Do not implement two writes to open a new intake year while closing another.
- Do not rely on the scheduled close as a security control.
- Do not create a `Reference Data Manager` role, a configuration approval chain or a `reference_data.*` capability string.
- Do not create a KenTender unit catalogue or an `other_unit` free-text field.
- Do not fork, override or duplicate the ERPNext `Fiscal Year`, `Company` or `UOM` DocTypes.
- Do not create downstream records when a fiscal year is added or intake is opened.
- Do not maintain legacy and Vue configuration screens in parallel.

---

## 17. Traceability and precedence

1. **KT-STD-001 v1.1** for document structure, design closed-input rules, the artboard shell, the shared fixture register, common page behaviour, the verification protocol, release evidence, seed conventions, universal prohibitions and error-contract conventions.
2. **AUTH-ADR-001** for business authority, role-bound assignment, Organisation Unit scope semantics, the shared resolver and the content of two System setup tabs.
3. **This document** for the site Procuring Entity, the Fiscal Year surface and its flags, Organisation Unit records, unit sourcing and the System setup page shell.
4. **Each business module** for its own states, windows, tasks and workflow.

Documents requiring a matching correction:

| Document | Required correction |
|---|---|
| NDS-CHG-001 | Add `kentender_needs_submission_closes_at` to the flag it consumes, so §11.2's **Open until 25 Nov 2026, 23:59 EAT** fixture is supported by the domain model. Confirm whether closing intake freezes existing Drafts or only blocks creation and submission. Cite KT-STD-001 in place of its own copies of the design rules, verification protocol and universal prohibitions. |
| CTX-CHG-001 | Withdraw in full. |
| PLN-CHG-001, BUD-CHG-001, STR-CHG-001, REQ-CHG-001, TPR-CHG-001 | Remove PE selectors, PE/FY context reads and KenTender `FinancialYear` references. Consume ERPNext `Fiscal Year` and `GetSiteConfiguration()`. Register any module intake flag under §4.2 rather than defining a local window record. |

---

## 18. Approval effect

Approved 3 September 2026. CFG-CHG-002 v0.8 supersedes v0.7 and all earlier versions in full, withdraws CTX-CHG-001, and becomes the only KenTender site-configuration document to consult.

This approval authorises: the site Procuring Entity as a Frappe Single DocType with first-run configuration and atomic root-unit creation; adoption of ERPNext `Fiscal Year` with the namespaced flag pattern and optional close instant; ERPNext `UOM` as the sole unit source; the `/app/system-setup` shell with four tabs; the commands in §7; removal of `PEFiscalYearContext`, the KenTender `FinancialYear` DocType, `ProcuringEntityVersion`, the PE register, the PE/FY selector, the `Reference Data Manager` role and every `/app/reference-data/*` route; and the seed and acceptance contracts in §13 and §14.
