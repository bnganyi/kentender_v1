# UI-00 — Tender Configurations Dashboard

**Project:** KenTender e-Procurement System  
**Module:** Tender Management  
**Menu location:** Tender Management → Tender Configurations  
**Surface type:** Application work queue  
**Status:** Revised screen specification v6  
**Design principle:** One dashboard, two row types: approved procurement packages and existing tender configurations

---

## 1. Purpose

The Tender Configurations Dashboard allows procurement users to:

1. create a tender configuration from an approved procurement package; and
2. continue, fix, review, or view existing tender configurations.

This dashboard is generic across STD families. It must support Information Technology first, but must not be named or designed as an IT-only dashboard.

---

## 2. Single User Decision

> What tender-configuration work needs my attention now?

This includes two cases:

| Case | Object shown | User action |
|---|---|---|
| No configuration exists yet | Approved Procurement Package | Create Tender Configuration |
| Configuration already exists | Tender Configuration | Continue, Fix, Submit, Open, or View |

Do not force both cases into one table model.

---

## 3. Position in the Journey

```text
Approved Procurement Package
→ Create Tender Configuration
→ Family-specific Tender Configuration Home
→ Configure tender-specific information
→ Run Readiness Check
→ Submit for Review
→ Preview Tender Document
→ Mark Ready for Publication
→ Tender Management publication workflow
```

UI-00 is the entry work queue. It is not a configuration screen.

---

## 4. User-Facing Terminology

Use these terms:

| Concept | User-facing term |
|---|---|
| Planning handoff | Approved Procurement Package |
| Configuration record | Tender Configuration |
| STD category | STD Family |
| Legal source document | Standard Tender Document |
| Configuration progress | Configuration Status |
| Required user action | Next Action |

Do not use these terms in the default UI:

```text
Tender Shell
TenderSTDInstance
STD binding
STD package code
schema version
hash
hydrator
iframe
configuration object
```

---

## 5. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | Work queues, filters, summary counts, create/open actions |
| Primary surface object | `TenderConfigurationsDashboard` |
| Shows | Approved packages ready for configuration and existing tender configurations |
| Creates | New Tender Configuration from Approved Procurement Package |
| Opens | Existing Tender Configuration |
| Editable here | Nothing except filters/view preferences |
| Must not own | tender profile fields, TDS values, requirements, schedules, inventory, price lines, evaluation criteria, forms, contract values, approval decision content, publication execution |

---

## 6. Page Header

Title:

```text
Tender Configurations
```

Subtitle:

```text
Create configurations from approved procurement packages and manage configurations already in progress.
```

Primary action:

```text
Create Tender Configuration
```

Primary action opens `UI-M01 — Create Tender Configuration`.

---

## 7. Required Page Structure

The page must have two clear work areas:

```text
Tender Configurations

[Create Tender Configuration]

Summary cards

Tabs:
- Ready to Configure
- In Progress
- Needs Attention
- Ready for Review
- Ready for Publication
- Completed

Table changes by selected tab.
```

The first tab is a procurement-package intake queue. The other tabs are tender-configuration queues.

---

## 8. Summary Cards

Show four compact cards only.

| Card | Exact label | Counts |
|---|---|---|
| Card 1 | Ready to Configure | Approved procurement packages without a tender configuration |
| Card 2 | In Progress | Existing configurations currently being completed |
| Card 3 | Needs Attention | Existing configurations with blockers, returned corrections, or unresolved required items |
| Card 4 | Ready for Review | Existing configurations that passed readiness checks and can be submitted or are awaiting review |

Do not use `Pending`. It is ambiguous and mixes package and configuration states.

---

## 9. Tabs

Use these tabs exactly:

| Tab | Object type | Meaning |
|---|---|---|
| Ready to Configure | Approved Procurement Package | Approved packages that do not yet have a tender configuration |
| In Progress | Tender Configuration | Configurations being completed |
| Needs Attention | Tender Configuration | Configurations with blockers, returned corrections, or required missing items |
| Ready for Review | Tender Configuration | Configurations ready to submit or already queued for review |
| Ready for Publication | Tender Configuration | Configurations approved and ready for publication handoff |
| Completed | Tender Configuration | Configurations already handed off or closed |

Do not use `Locked`, `Ready`, `Pending`, or raw enum labels as tab names.

---

## 10. Filters

Required filters:

| Filter | Applies to | Options / behavior |
|---|---|---|
| Search | All tabs | Search by procurement package ref, package title, tender title, procuring entity, or configuration ref |
| STD Family | All tabs | All, Information Technology, Works, Goods, Consultancy, Non-Consultancy |
| Procuring Entity | All tabs | Dropdown from available entities |
| Procurement Method | All tabs | Dropdown from configured methods |
| Issue Status | Configuration tabs only | All, Has Blockers, Has Warnings, No Issues |

Do not show `Configuration Status` as a filter if the active tab already represents status. It is redundant and increases confusion.

---

## 11. Table A — Ready to Configure

When the active tab is `Ready to Configure`, rows are **Approved Procurement Packages**, not tender configurations.

Use this table exactly:

| Column | Exact label | Example | Rule |
|---|---|---|---|
| 1 | Procurement Package Ref | PP-ICT-2024-009 | Primary upstream reference from Planning |
| 2 | Package Title | Data Center Hardware Refresh | Title from the approved procurement package |
| 3 | STD Family | Information Technology | Applicable STD family |
| 4 | Procuring Entity | National Treasury | Owning entity |
| 5 | Procurement Method | Open National Tender | Approved method |
| 6 | Approval Date | 2026-07-12 | Date package became eligible for configuration |
| 7 | Action | Create Configuration | Opens create modal with package preselected |

Do not show these columns in this tab because no configuration exists yet:

```text
Configuration Ref
Configuration Status
Issues
Next Configuration Step
Last Configured
Blockers
Warnings
Readiness
Review Status
```

### Sample rows

| Procurement Package Ref | Package Title | STD Family | Procuring Entity | Procurement Method | Approval Date | Action |
|---|---|---|---|---|---|---|
| PP-ICT-2024-009 | Data Center Hardware Refresh | Information Technology | National Treasury | Open National Tender | 2026-07-12 | Create Configuration |
| PP-WKS-2024-014 | County Office Renovation Works | Works | Ministry of Public Works | Open National Tender | 2026-07-10 | Create Configuration |
| PP-GDS-2024-021 | Supply of Office Furniture | Goods | Ministry of Education | Request for Quotations | 2026-07-09 | Create Configuration |

---

## 12. Table B — Existing Tender Configurations

When the active tab is any of these tabs, rows are **Tender Configurations**:

```text
In Progress
Needs Attention
Ready for Review
Ready for Publication
Completed
```

Use this table exactly:

| Column | Exact label | Example | Rule |
|---|---|---|---|
| 1 | Configuration Ref | TCFG-2026-009 | Primary configuration reference |
| 2 | Procurement Package Ref | PP-ICT-2024-009 | Source package reference |
| 3 | Tender Title | Data Center Hardware Refresh | Tender title from the configuration/profile |
| 4 | STD Family | Information Technology | Applicable STD family |
| 5 | Procuring Entity | National Treasury | Owning entity |
| 6 | Status | In Progress | Human-readable configuration status |
| 7 | Issues | 0 Blockers / 2 Warnings | Summary only |
| 8 | Last Updated | 2026-07-17 10:45 EAT | Date/time with timezone |
| 9 | Next Action | Continue Configuration | One clear row action |

### Sample rows

| Configuration Ref | Procurement Package Ref | Tender Title | STD Family | Procuring Entity | Status | Issues | Last Updated | Next Action |
|---|---|---|---|---|---|---|---|---|
| TCFG-2026-009 | PP-ICT-2024-009 | Data Center Hardware Refresh | Information Technology | National Treasury | In Progress | 0 Blockers / 2 Warnings | 2026-07-17 10:45 EAT | Continue Configuration |
| TCFG-2026-011 | PP-ICT-2024-011 | ERP Implementation Services | Information Technology | National Social Security Fund | Needs Attention | 2 Blockers / 1 Warning | 2026-07-17 09:20 EAT | Fix Issues |
| TCFG-2026-015 | PP-WKS-2024-014 | County Office Renovation Works | Works | Ministry of Public Works | Ready for Review | 0 Blockers / 0 Warnings | 2026-07-16 16:10 EAT | Submit for Review |

---

## 13. Row Actions

Each row must have one primary action.

| Active tab / row condition | Button label | Behavior |
|---|---|---|
| Ready to Configure | Create Configuration | Opens `UI-M01` with the procurement package preselected |
| In Progress | Continue Configuration | Opens family-specific Tender Configuration Home |
| Needs Attention | Fix Issues | Opens Tender Configuration Home with issue focus |
| Ready for Review | Submit for Review | Opens review submission confirmation |
| Ready for Publication | Open Handoff | Opens publication handoff view |
| Completed | View Configuration | Opens read-only configuration summary |

Secondary actions may be inside a row menu:

```text
View Details
View Readiness Report
View Audit Trail
```

Do not show multiple competing primary actions in one row.

---

## 14. Status Labels

Use only these configuration status labels for existing configurations:

| Label | Meaning |
|---|---|
| In Progress | Configuration is being completed |
| Needs Attention | Blockers, returned corrections, or required missing items exist |
| Ready for Review | Configuration passed readiness checks and can enter review |
| Under Review | Submitted and awaiting reviewer action |
| Ready for Publication | Approved and ready for publication handoff |
| Completed | Handoff completed or configuration closed |

`Ready to Configure` is not a configuration status. It is a tab/work queue for approved procurement packages without configurations.

---

## 15. Create Configuration Modal Entry

The primary button and `Create Configuration` row action both open `UI-M01 — Create Tender Configuration`.

The modal must start from:

```text
Approved Procurement Package
```

not:

```text
Tender Shell
Tender to Configure
Tender Record
```

If the row action is clicked from `Ready to Configure`, the selected procurement package is prefilled and read-only unless the user changes it intentionally.

After package selection, the modal shows read-only derived values:

```text
Planning Package Ref
Procuring Entity
Procurement Method
STD Family
Standard Tender Document
```

If multiple Standard Tender Documents are valid for the package, selection is allowed only where policy permits and the user has authority.

---

## 16. Row Detail Drawer

A row drawer may be used for quick context.

### Drawer for Ready to Configure package rows

Allowed content:

```text
Procurement Package Ref
Package Title
STD Family
Procuring Entity
Procurement Method
Approval Date
Standard Tender Document
Action: Create Configuration
```

### Drawer for existing configuration rows

Allowed content:

```text
Configuration Ref
Procurement Package Ref
Tender Title
STD Family
Standard Tender Document
Procuring Entity
Procurement Method
Status
Issue Summary
Next Action
Last Updated
```

Forbidden drawer content:

```text
TDS fields
requirement rows
implementation phases
inventory records
price lines
evaluation marks
forms checklist
contract clauses
STD hashes
schema metadata
raw audit events
```

---

## 17. Empty States

### Ready to Configure tab empty

Title:

```text
No approved procurement packages ready to configure
```

Body:

```text
Tender configurations can only be created from approved procurement packages that have not already been configured.
```

Primary action:

```text
Refresh
```

Optional secondary action:

```text
View Procurement Packages
```

### Configuration tabs empty

Title:

```text
No tender configurations found
```

Body:

```text
No tender configurations match the selected tab and filters.
```

Primary action:

```text
Clear Filters
```

---

## 18. Forbidden Complexity

Do not show on this screen:

- detailed configuration forms;
- STD clause trees;
- source-document hashes;
- rule IDs;
- schema versions;
- tender shell references;
- TenderSTDInstance references;
- price schedule line items;
- evaluation score matrices;
- bidder submission forms;
- contract clauses;
- publication execution controls;
- raw audit logs.

This screen is a work queue only.

---

## 19. API Payload

The API must explicitly separate package rows from configuration rows.

Preferred shape:

```json
{
  "summary": {
    "ready_to_configure_count": 4,
    "in_progress_count": 8,
    "needs_attention_count": 3,
    "ready_for_review_count": 2,
    "ready_for_publication_count": 1,
    "completed_count": 12
  },
  "filters": {
    "std_families": ["Information Technology", "Works", "Goods", "Consultancy", "Non-Consultancy"],
    "procuring_entities": [],
    "procurement_methods": []
  },
  "ready_to_configure_packages": [
    {
      "row_type": "approved_procurement_package",
      "procurement_package_ref": "PP-ICT-2024-009",
      "package_title": "Data Center Hardware Refresh",
      "std_family": "Information Technology",
      "standard_tender_document_label": "IT Standard Tender Document — April 2022",
      "procuring_entity_name": "National Treasury",
      "procurement_method_label": "Open National Tender",
      "approval_date": "2026-07-12",
      "action_label": "Create Configuration",
      "action_route": "open_create_configuration_modal"
    }
  ],
  "configurations": [
    {
      "row_type": "tender_configuration",
      "configuration_ref": "TCFG-2026-009",
      "procurement_package_ref": "PP-ICT-2024-009",
      "tender_title": "Data Center Hardware Refresh",
      "std_family": "Information Technology",
      "standard_tender_document_label": "IT Standard Tender Document — April 2022",
      "procuring_entity_name": "National Treasury",
      "procurement_method_label": "Open National Tender",
      "status_label": "In Progress",
      "blocker_count": 0,
      "warning_count": 2,
      "last_updated_at": "2026-07-17T10:45:00+03:00",
      "next_action_label": "Continue Configuration",
      "next_action_route": "/desk/tender-configuration-home?configuration_id=TCFG-2026-009"
    }
  ]
}
```

Do not make the frontend infer whether a row is a package or a configuration from missing fields.

---

## 20. Stitch Prompt

```text
Design UI-00 for KenTender.

Screen name: Tender Configurations
Menu location: Tender Management → Tender Configurations

User goal:
Create tender configurations from approved procurement packages and manage configurations already in progress.

Single user decision:
What tender-configuration work needs my attention now?

Important model rule:
This dashboard has two row types. The Ready to Configure tab shows approved procurement packages that do not yet have tender configurations. All other tabs show existing tender configurations. Do not use one table structure for both.

Header:
- Title: Tender Configurations
- Subtitle: Create configurations from approved procurement packages and manage configurations already in progress.
- Primary button: Create Tender Configuration

Summary cards:
- Ready to Configure
- In Progress
- Needs Attention
- Ready for Review

Tabs:
- Ready to Configure
- In Progress
- Needs Attention
- Ready for Review
- Ready for Publication
- Completed

Filters:
- Search
- STD Family
- Procuring Entity
- Procurement Method
- Issue Status, shown only for configuration tabs

Ready to Configure table columns:
- Procurement Package Ref
- Package Title
- STD Family
- Procuring Entity
- Procurement Method
- Approval Date
- Action

Ready to Configure example row:
- Procurement Package Ref: PP-ICT-2024-009
- Package Title: Data Center Hardware Refresh
- STD Family: Information Technology
- Procuring Entity: National Treasury
- Procurement Method: Open National Tender
- Approval Date: 2026-07-12
- Action: Create Configuration

Existing configuration table columns:
- Configuration Ref
- Procurement Package Ref
- Tender Title
- STD Family
- Procuring Entity
- Status
- Issues
- Last Updated
- Next Action

Existing configuration example row:
- Configuration Ref: TCFG-2026-009
- Procurement Package Ref: PP-ICT-2024-009
- Tender Title: Data Center Hardware Refresh
- STD Family: Information Technology
- Procuring Entity: National Treasury
- Status: In Progress
- Issues: 0 Blockers / 2 Warnings
- Last Updated: 2026-07-17 10:45 EAT
- Next Action: Continue Configuration

Allowed row action labels:
- Create Configuration
- Continue Configuration
- Fix Issues
- Submit for Review
- Open Handoff
- View Configuration

Do not show Pending as a tab, card, or status label.
Do not show Tender Shell, TenderSTDInstance, STD binding, STD package code, schema version, hashes, rule IDs, configuration object, or any internal architecture terms.
Do not show detailed TDS fields, requirements, schedules, inventory, price lines, evaluation marks, forms, contract clauses, approval forms, publication controls, or audit logs.
```

---

## 21. Cursor Prompt

```text
Implement UI-00 — Tender Configurations Dashboard for KenTender.

Architecture:
Use the approved production UI architecture. Do not use iframe + Tailwind CDN for production. Use local KenTender UI bundle/styles and Frappe APIs.

Menu location:
Tender Management → Tender Configurations

Purpose:
Create tender configurations from approved procurement packages and manage configurations already in progress.

Critical model rule:
This dashboard has two row types:
1. Approved procurement packages without configurations.
2. Existing tender configurations.

Do not force both row types into one table schema.

Header:
- Title: Tender Configurations
- Subtitle: Create configurations from approved procurement packages and manage configurations already in progress.
- Primary button: Create Tender Configuration

Primary button behavior:
Open UI-M01 — Create Tender Configuration.
The modal starts from Approved Procurement Package.
Do not use Tender Shell or Tender to Configure language.

Summary cards:
- Ready to Configure
- In Progress
- Needs Attention
- Ready for Review

Tabs:
- Ready to Configure
- In Progress
- Needs Attention
- Ready for Review
- Ready for Publication
- Completed

Ready to Configure tab:
Render approved procurement packages only.
Columns:
- Procurement Package Ref
- Package Title
- STD Family
- Procuring Entity
- Procurement Method
- Approval Date
- Action

Do not render Configuration Ref, Configuration Status, Issues, Last Updated, or Next Configuration Step in Ready to Configure.

Configuration tabs:
Render existing tender configurations only.
Columns:
- Configuration Ref
- Procurement Package Ref
- Tender Title
- STD Family
- Procuring Entity
- Status
- Issues
- Last Updated
- Next Action

Allowed action labels:
- Create Configuration
- Continue Configuration
- Fix Issues
- Submit for Review
- Open Handoff
- View Configuration

Forbidden:
- Do not show Pending as a label.
- Do not render detailed configuration fields.
- Do not render internal terms: Tender Shell, TenderSTDInstance, STD binding, STD package code, schema version, hash, rule ID, hydrator, iframe.
- Do not render TDS fields, requirement rows, implementation phases, inventory rows, price lines, evaluation marks, forms checklist, contract clauses, approval decision content, publication execution controls, or raw audit logs.

API requirements:
The dashboard endpoint must explicitly return row_type or separate arrays:
- ready_to_configure_packages[]
- configurations[]

Do not let the frontend guess row type from missing fields.

Acceptance criteria:
1. Page title is Tender Configurations.
2. There is no Pending tab, card, or status label.
3. Ready to Configure shows approved procurement packages only.
4. Configuration tabs show tender configurations only.
5. Ready to Configure uses package-specific columns.
6. Configuration tabs use configuration-specific columns.
7. The create flow starts from Approved Procurement Package.
8. No internal architecture terms appear.
9. No detailed configuration data appears.
10. A user can identify the correct next action within 10 seconds.
```

---

## 22. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Generic naming | Page title is `Tender Configurations`, not `IT Tender Configurations` |
| Menu correctness | Screen is under `Tender Management → Tender Configurations` |
| No ambiguous pending label | `Pending` does not appear as tab, card, or status |
| Row-type clarity | Ready to Configure rows are approved procurement packages |
| Configuration clarity | Other tabs show tender configurations only |
| Correct package columns | Ready to Configure table does not show configuration-only fields |
| Correct configuration columns | Configuration tabs include Configuration Ref, Status, Issues, Last Updated, and Next Action |
| Creation source | Create flow starts from `Approved Procurement Package` |
| Future STD support | Both tables include `STD Family` |
| Simplicity | No detailed configuration forms appear |
| Action clarity | Each row has one primary action |
| No internal terminology | Forbidden backend terms are absent |

---

## 23. Final Rule

If a row does not yet have a tender configuration, treat it as an **Approved Procurement Package**, not as a pending configuration.

If a field does not help the user choose the next dashboard action, remove it from UI-00.
