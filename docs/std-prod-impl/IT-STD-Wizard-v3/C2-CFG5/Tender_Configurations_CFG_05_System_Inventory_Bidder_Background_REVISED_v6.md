# CFG-05 — System Inventory & Bidder Background v6

**Product:** KenTender  
**Area:** Tender Management → Tender Configurations  
**Surface type:** Configuration step  
**Configuration step:** CFG-05  
**Screen name:** System Inventory & Bidder Background  
**STD family:** Information Technology  
**Status:** Revised v6 specification  

---

## 1. Purpose

Describe the existing environment, inventory context, sites, integrations, data, and background information bidders need in order to prepare a responsive IT tender.

This screen helps the procurement user answer one question:

> What bidder-relevant environment and inventory information must be disclosed for this IT tender?

---

## 2. User-facing entry path

The user reaches this screen from:

`Tender Management → Tender Configurations → Tender Configuration Home → System Inventory & Bidder Background`

This screen is available after **CFG-03 — IT Requirements** and **CFG-04 — Implementation Schedule** have enough information to identify the environment, sites, components, integrations, data, or context bidders must understand.

---

## 3. STD grounding

This screen maps primarily to:

- **Section VIII — System Inventory Tables**
- **Section IX — Background and Informational Materials**

It may also reference configured IT requirements and implementation milestones where context is needed for bidder understanding.

Important rule:

> Background information must help bidders understand the tender context. It must not create new technical requirements by itself. Binding requirements belong in **CFG-03 — IT Requirements**.

---

## 4. Screen ownership

| Area | Rule |
|---|---|
| Owns | Bidder-relevant inventory items, sites/locations, existing systems context, integration context, data migration context, infrastructure context, user/location context, support/licensing context, disclosure-safe background notes |
| Does not own | Tender identity, TDS values, detailed requirement wording, implementation milestone definitions, price schedule rows, evaluated-price inclusion, scoring, bidder form checklist, SCC values, review decisions, publication actions, post-award asset management |
| Reads from | Approved Procurement Package, Tender Profile, Tender Data Sheet, IT Requirements, Implementation Schedule, selected IT Standard Tender Document |
| Feeds | Price Schedule, Evaluation Setup, Forms & Evidence, Contract Values, Readiness Check, Tender Document Preview |

---

## 5. Page header

**Title:**

`System Inventory & Bidder Background`

**Subtitle:**

`Describe the systems, sites, integrations, data, and background context bidders need to understand the IT tender.`

**Primary actions:**

- `Add Inventory Item`
- `Add Background Note`
- `Save Inventory & Background`
- `Run Check`
- `Continue to Price Schedule`

**Secondary action:**

- `Back to Configuration Home`

Do not use:

- `Asset Register`
- `CMDB`
- `Security Console`
- `Pricing Inventory`
- `Contract Asset Management`
- `Implementation Tracking`

---

## 6. Context strip

Show only:

| Label | Example |
|---|---|
| Procurement Package Ref | `PP-ICT-2024-009` |
| Tender Title | `Data Center Hardware Refresh` |
| Procuring Entity | `National Treasury` |
| Procurement Method | `Open National Tender` |
| STD Family | `Information Technology` |
| Standard Tender Document | `IT Standard Tender Document — April 2022` |
| Configuration Status | `In Progress` |
| Issues | `2 Blockers / 1 Warning` |

Do not show hashes, rule IDs, binding IDs, schema versions, internal object names, or technical metadata.

---

## 7. Main layout

Use a focused disclosure layout:

1. Page header and actions
2. Tender context strip
3. Disclosure guidance banner
4. Category filters
5. Inventory and background table
6. Right guidance panel
7. Footer action bar
8. Add/Edit drawer opened only when creating or editing an item

Do not show full pricing forms, evaluation scores, SCC clauses, post-award asset management records, operational secrets, network diagrams, passwords, IP addresses, vulnerability details, or internal security procedures.

---

## 8. Disclosure guidance banner

Show this banner near the top of the screen:

`Only include information bidders need to prepare a responsive tender. Do not disclose passwords, secret keys, private IP addresses, vulnerability details, or internal security procedures.`

Optional secondary text:

`If a detail creates a binding obligation, configure it in IT Requirements instead of only describing it as background.`

---

## 9. Category filters

Use these exact category filters:

| Filter | Meaning |
|---|---|
| `All` | Shows all inventory and background records. |
| `Systems in Scope` | Existing or target systems bidders must consider. |
| `Infrastructure Environment` | Servers, hosting, network, storage, data center, cloud, or platform context. |
| `Sites & Users` | Locations, user groups, branches, departments, or usage context. |
| `Integrations` | Interfaces, systems, APIs, or data exchange points. |
| `Data Migration` | Data sources, volumes, migration expectations, and cleansing context. |
| `Licensing & Support` | Existing licences, support arrangements, renewals, or warranty context. |
| `Background Notes` | Informational material that helps bidders understand context but does not create requirements. |
| `Out of Scope` | Items expressly excluded from the tender scope. |

Do not use commercial pricing categories such as `Supply & Installation` or `Recurrent` as the main filters on this screen. Those belong in **CFG-06 — Price Schedule**.

---

## 10. Main table

Show this exact table.

| Column | Purpose |
|---|---|
| ID | Inventory/background reference, for example `INV-001` or `BG-001` |
| Item | Clear bidder-facing item or context title |
| Category | One of the approved screen categories |
| Scope | `In scope`, `Context only`, or `Out of scope` |
| Bidder Consideration | What bidders should consider when preparing the tender |
| Disclosure Status | Whether the information is safe to disclose |
| Price Link | Lightweight reference only |
| Status | Local completeness status |
| Actions | `Edit`, `Fix`, or `Review` |

Do not include price amount, evaluated-price inclusion, marks, pass scores, contract clause references, implementation progress, asset ownership status, or security classification details beyond safe disclosure labels.

---

## 11. Sample rows

Use these sample rows in Stitch/Cursor fixtures unless a better approved seed fixture is supplied:

| ID | Item | Category | Scope | Bidder Consideration | Disclosure Status | Price Link | Status | Action |
|---|---|---|---|---|---|---|---|---|
| INV-001 | Existing Server Room | Infrastructure Environment | Context only | Bidder should account for installation constraints and rack space limitations. | Safe to disclose | May affect price schedule | Complete | Edit |
| INV-002 | Head Office User Groups | Sites & Users | In scope | Bidder should size the solution for head office users and support needs. | Needs disclosure review | May affect price schedule | Needs attention | Fix |
| INV-003 | Finance System Integration | Integrations | In scope | Bidder should provide integration approach with the existing finance system. | Safe to disclose | May affect price schedule | Complete | Edit |
| INV-004 | Legacy Asset Database | Data Migration | In scope | Bidder should plan data migration, validation, and reconciliation. | Safe to disclose | May affect price schedule | Complete | Edit |
| INV-005 | Existing Antivirus Licence | Licensing & Support | Context only | Bidder should note existing endpoint protection context but propose required support separately. | Safe to disclose | No price link expected | Complete | Review |
| BG-001 | Current ICT Operating Environment | Background Notes | Context only | Bidder should understand current operating model and institutional context. | Safe to disclose | No price link expected | Complete | Edit |
| BG-002 | Restricted Network Details | Background Notes | Context only | Sensitive technical details should not be disclosed in the tender document. | Remove sensitive detail | No price link expected | Needs attention | Fix |
| INV-006 | Disaster Recovery Site | Out of Scope | Out of scope | Bidder should not price or propose work for this site unless later added by addendum. | Safe to disclose | No price link expected | Complete | Review |

---

## 12. Scope values

Allowed scope values:

| Scope | Meaning |
|---|---|
| `In scope` | The item is relevant to the tender scope and may affect requirements, pricing, evidence, or contract values. |
| `Context only` | The item helps bidders understand the environment but does not create a requirement by itself. |
| `Out of scope` | The item is expressly excluded from this tender. |

Do not use vague scope values such as `Relevant`, `Applicable`, `Active`, or `Optional`.

---

## 13. Disclosure status values

Allowed disclosure status values:

| Disclosure Status | Meaning |
|---|---|
| `Safe to disclose` | The information may appear in the tender document. |
| `Needs disclosure review` | The information may be useful but should be reviewed before publication. |
| `Remove sensitive detail` | The item contains sensitive information that must not be published as shown. |
| `Not configured` | Disclosure status has not been set. |

Do not expose passwords, keys, usernames, private IP addresses, detailed firewall rules, vulnerability information, internal security procedures, or sensitive network topology in the default UI or generated tender document.

---

## 14. Price Link behavior

`Price Link` is a lightweight reference only.

Allowed values:

| Price Link | Meaning |
|---|---|
| `May affect price schedule` | The item may require a related price line in CFG-06. |
| `Linked in Price Schedule` | A related price line already exists in CFG-06. |
| `No price link expected` | The item is context only or not priced. |
| `To be reviewed` | The user must decide whether pricing is affected. |

Do not configure pricing basis, quantities, units, tax treatment, evaluated-price inclusion, or price amount on this screen. Those belong in **CFG-06 — Price Schedule**.

---

## 15. Add/Edit drawer

The drawer must use this exact structure.

### 15.1 Item identity

| Field label | Type | Rule |
|---|---|---|
| Item Title | Text | Required |
| Category | Select | Required; use approved categories only |
| Scope | Select | Required |
| Item Description | Text area | Required |

### 15.2 Bidder context

| Field label | Type | Rule |
|---|---|---|
| Bidder Consideration | Text area | Required |
| Related IT Requirement | Reference / select | Optional |
| Related Implementation Milestone | Reference / select | Optional |

### 15.3 Inventory/background details

Use only the fields relevant to the selected category.

| Field label | Type | Rule |
|---|---|---|
| Location / Site | Text / select | Optional |
| Existing System Name | Text | Optional |
| Estimated Volume / Count | Text | Optional; must be bidder-safe |
| Integration Point | Text | Optional |
| Data Source | Text | Optional |
| Support / Licence Context | Text area | Optional |
| Out-of-Scope Note | Text area | Required when Scope is `Out of scope` |

Do not require all fields for all categories. Keep the drawer short and category-sensitive.

### 15.4 Disclosure

| Field label | Type | Rule |
|---|---|---|
| Disclosure Status | Select | Required |
| Disclosure Note | Text area | Required if disclosure status is `Needs disclosure review` or `Remove sensitive detail` |

### 15.5 References

Show only compact references:

| Label | Allowed text |
|---|---|
| IT Requirements | `Linked to IT Requirement` / `No requirement link selected` |
| Implementation Schedule | `Linked to milestone` / `No milestone link selected` |
| Price Schedule | `May affect price schedule` / `Linked in Price Schedule` / `No price link expected` |
| Contract Values | `May carry into contract values` / `No contract carry-forward expected` |

Do not use the drawer to configure price lines, evaluation marks, formal submission checklist rows, SCC clauses, contract obligations, or post-award asset records.

---

## 16. Source and summary behavior

This screen must not show magical summary values.

Every displayed summary value must be either:

- derived from configured inventory/background records;
- entered by the user on this screen;
- read from approved upstream context; or
- shown as `Not configured`.

Allowed source labels:

| Source label | Meaning | Editable here? |
|---|---|---|
| `User-entered` | User entered or changed the value on this screen. | Yes |
| `From Approved Procurement Package` | Comes from the approved planning handoff. | No; change upstream if wrong |
| `Suggested from IT Requirements` | Suggested from configured requirements. | Yes, as local context |
| `Suggested from Implementation Schedule` | Suggested from configured milestones or delivery assumptions. | Yes, as local context |
| `Not configured` | No value exists yet. | User must complete it if required |

Do not display realistic-looking values such as user counts, device counts, branch counts, security classifications, data residency, or access methods unless those values have a configured source.

---

## 17. Status labels

Use only:

| Status | Meaning |
|---|---|
| Complete | Required item description, scope, bidder consideration, and disclosure status are set. |
| Needs attention | Required information is missing or disclosure review is needed. |
| In progress | Item has been started but is incomplete. |
| Not started | Placeholder exists but has no meaningful content. |

Do not use:

- `Valid`
- `Ready`
- `Locked`
- `Approved`
- `Published`
- `Priced`
- `Scored`
- raw rule IDs

---

## 18. Right guidance panel

Panel title:

`Inventory & Background Guidance`

Panel text:

`Describe the environment bidders need to understand. Keep binding obligations in IT Requirements and commercial pricing in Price Schedule.`

Show compact guidance rows:

| Label | Text |
|---|---|
| What this affects | `Bidder understanding, price schedule structure, evidence expectations, contract values, and tender preview.` |
| Used later by | `Price Schedule, Evaluation Setup, Forms & Evidence, Contract Values, and Readiness Check.` |
| Not configured here | `Technical requirements, price amounts, scoring, submission forms, SCC values, security secrets, and post-award asset records.` |

---

## 19. Validation behavior

This screen may show only local summary validation.

Allowed messages:

- `2 items need disclosure review.`
- `1 in-scope item is missing bidder consideration.`
- `1 background note may create a requirement. Move the obligation to IT Requirements.`
- `Inventory and background complete.`

Do not show rule IDs, clause IDs, render-block diagnostics, hashes, schema errors, private security details, or internal object names in the default UI.

Detailed findings belong in the readiness report.

---

## 20. Downstream impact

This screen feeds:

- **CFG-06 — Price Schedule** for inventory/context that may require supply, installation, recurrent, support, licence, migration, integration, or site-related price items
- **CFG-07 — Evaluation Setup** where bidder understanding of environment affects evaluation criteria or qualification context
- **CFG-08 — Forms & Evidence** for bidder submission evidence related to integrations, migration, support, site readiness, or disclosure-sensitive background
- **CFG-09 — Contract Values** for background/inventory items that carry into contract appendices, delivery obligations, support obligations, or acceptance context
- **Readiness Check** for completeness, consistency, and disclosure safety
- **Tender Document Preview** for rendered Section VIII and Section IX content

This screen must not configure:

- tender identity or procurement package context
- Tender Data Sheet values
- binding technical requirements
- delivery milestone definitions
- price rows, quantities, units, tax treatment, evaluated-price inclusion, or price amounts
- evaluation marks, pass marks, or scoring formulas
- bidder submission checklist rows
- SCC values or contract clause text
- review decisions
- publication actions
- post-award asset management, inspection, operations, support ticketing, or contract administration

---

## 21. API shape

```json
{
  "configuration_id": "TCFG-2024-0009",
  "procurement_package_ref": "PP-ICT-2024-009",
  "tender_title": "Data Center Hardware Refresh",
  "procuring_entity_name": "National Treasury",
  "procurement_method_label": "Open National Tender",
  "std_family_label": "Information Technology",
  "standard_tender_document_label": "IT Standard Tender Document — April 2022",
  "configuration_status_label": "In Progress",
  "blocker_count": 2,
  "warning_count": 1,
  "category_filter": "All",
  "items": [
    {
      "item_id": "INV-001",
      "item_title": "Existing Server Room",
      "category_label": "Infrastructure Environment",
      "scope_label": "Context only",
      "bidder_consideration": "Bidder should account for installation constraints and rack space limitations.",
      "disclosure_status_label": "Safe to disclose",
      "price_link_label": "May affect price schedule",
      "status_label": "Complete",
      "action_label": "Edit"
    },
    {
      "item_id": "BG-002",
      "item_title": "Restricted Network Details",
      "category_label": "Background Notes",
      "scope_label": "Context only",
      "bidder_consideration": "Sensitive technical details should not be disclosed in the tender document.",
      "disclosure_status_label": "Remove sensitive detail",
      "price_link_label": "No price link expected",
      "status_label": "Needs attention",
      "action_label": "Fix"
    }
  ]
}
```

---

## 22. Stitch prompt

```text
Design CFG-05 — System Inventory & Bidder Background for KenTender Tender Configurations.

Screen purpose:
Describe the systems, sites, integrations, data, and background context bidders need to understand the IT tender.

User decision:
What bidder-relevant environment and inventory information must be disclosed for this IT tender?

Header:
Title: System Inventory & Bidder Background
Subtitle: Describe the systems, sites, integrations, data, and background context bidders need to understand the IT tender.

Context strip fields:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Configuration Status
- Issues

Show this disclosure guidance banner:
Only include information bidders need to prepare a responsive tender. Do not disclose passwords, secret keys, private IP addresses, vulnerability details, or internal security procedures.

Category filters:
- All
- Systems in Scope
- Infrastructure Environment
- Sites & Users
- Integrations
- Data Migration
- Licensing & Support
- Background Notes
- Out of Scope

Main table columns:
- ID
- Item
- Category
- Scope
- Bidder Consideration
- Disclosure Status
- Price Link
- Status
- Actions

Use these sample rows:
1. INV-001 | Existing Server Room | Infrastructure Environment | Context only | Bidder should account for installation constraints and rack space limitations. | Safe to disclose | May affect price schedule | Complete | Edit
2. INV-002 | Head Office User Groups | Sites & Users | In scope | Bidder should size the solution for head office users and support needs. | Needs disclosure review | May affect price schedule | Needs attention | Fix
3. INV-003 | Finance System Integration | Integrations | In scope | Bidder should provide integration approach with the existing finance system. | Safe to disclose | May affect price schedule | Complete | Edit
4. INV-004 | Legacy Asset Database | Data Migration | In scope | Bidder should plan data migration, validation, and reconciliation. | Safe to disclose | May affect price schedule | Complete | Edit
5. BG-001 | Current ICT Operating Environment | Background Notes | Context only | Bidder should understand current operating model and institutional context. | Safe to disclose | No price link expected | Complete | Edit
6. BG-002 | Restricted Network Details | Background Notes | Context only | Sensitive technical details should not be disclosed in the tender document. | Remove sensitive detail | No price link expected | Needs attention | Fix

Right guidance panel:
Title: Inventory & Background Guidance
Text: Describe the environment bidders need to understand. Keep binding obligations in IT Requirements and commercial pricing in Price Schedule.

Drawer sections:
1. Item identity
2. Bidder context
3. Inventory/background details
4. Disclosure
5. References

Primary buttons:
- Add Inventory Item
- Add Background Note
- Save Inventory & Background
- Run Check
- Continue to Price Schedule

Do not show price amounts, evaluation marks, SCC clauses, asset management records, passwords, secret keys, private IP addresses, vulnerability details, detailed firewall rules, internal security procedures, hashes, rule IDs, binding IDs, schema versions, or internal object names.
```

---

## 23. Cursor prompt

```text
Implement CFG-05 — System Inventory & Bidder Background in the Tender Configurations module.

This screen describes bidder-relevant systems, sites, integrations, data, inventory context, and background information. It is not a CMDB, asset register, price schedule, evaluation screen, contract administration screen, security console, or post-award operations screen.

Route:
Tender Management → Tender Configurations → Tender Configuration Home → System Inventory & Bidder Background

Primary object:
SystemInventoryBackgroundConfiguration

Screen owns:
- inventory/background item title
- category
- scope
- item description
- bidder consideration
- related IT requirement reference
- related implementation milestone reference
- category-sensitive inventory/background details
- disclosure status
- disclosure note
- lightweight price-link reference

Screen does not own:
- Tender Profile values
- Tender Data Sheet values
- binding IT requirement text
- implementation milestone definitions
- price schedule rows
- price amounts
- pricing basis
- quantities/units for bidder pricing
- evaluated-price inclusion
- evaluation marks or pass scores
- bidder submission checklist rows
- SCC values or contract clause text
- review decisions
- publication actions
- post-award asset management
- inspection records
- operations records
- internal security secrets

Required table columns:
- ID
- Item
- Category
- Scope
- Bidder Consideration
- Disclosure Status
- Price Link
- Status
- Actions

Approved category filters:
- All
- Systems in Scope
- Infrastructure Environment
- Sites & Users
- Integrations
- Data Migration
- Licensing & Support
- Background Notes
- Out of Scope

Approved scope values:
- In scope
- Context only
- Out of scope

Approved disclosure status values:
- Safe to disclose
- Needs disclosure review
- Remove sensitive detail
- Not configured

Approved price link values:
- May affect price schedule
- Linked in Price Schedule
- No price link expected
- To be reviewed

Status labels:
- Complete
- Needs attention
- In progress
- Not started

Data rules:
- Do not display any summary value unless it is source-backed or explicitly Not configured.
- Do not show magical values such as user counts, device counts, branch counts, access methods, security classifications, or data residency unless they come from configured records or approved upstream data.
- Background notes must not create binding requirements. If a background note creates an obligation, validation should tell the user to move the obligation to IT Requirements.
- Price Link is a lightweight reference only; actual price configuration belongs in CFG-06.
- Do not display passwords, secret keys, usernames, private IP addresses, detailed firewall rules, vulnerability details, internal security procedures, or sensitive topology.

Primary buttons:
- Add Inventory Item
- Add Background Note
- Save Inventory & Background
- Run Check
- Continue to Price Schedule

Acceptance criteria:
- User can understand this screen is for bidder-relevant environment and background disclosure.
- The main table uses the exact approved columns.
- The first tab/filter does not use Supply & Installation or Recurrent as primary categories.
- Pricing is referenced lightly only and configured in CFG-06.
- Binding requirements are not created through background notes.
- Every displayed summary value is source-backed or shown as Not configured.
- No secret or sensitive operational detail appears in the default UI.
- No pricing, evaluation, SCC, review, publication, hash, rule ID, schema version, binding ID, or internal system object appears in the default UI.
```

---

## 24. Acceptance checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell the screen is for deciding what bidder-relevant inventory/background information to disclose. |
| STD grounding | Screen maps to Section VIII and Section IX of the IT STD. |
| Ownership clarity | Screen owns inventory/background disclosure only. |
| No magical values | Summary and detail values are source-backed or shown as `Not configured`. |
| Disclosure safety | Sensitive operational details are blocked or flagged for review. |
| Price boundary | Pricing is referenced lightly only; no price lines or amounts are configured. |
| Requirement boundary | Binding obligations are configured in IT Requirements, not hidden in background notes. |
| Downstream awareness | Screen references downstream use without configuring price, evaluation, forms, contract, or review details. |
| Simplicity | No CMDB, asset register, security console, or post-award operations content appears. |
| Prompt precision | Stitch and Cursor prompts contain exact labels, columns, sample rows, statuses, actions, and forbidden content. |

---

## 25. Final rule

If a field does not help bidders understand the IT environment, inventory, sites, integrations, data, or background context safely, remove it from CFG-05.
