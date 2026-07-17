# Tender Configurations — CFG-09 Contract Values v6

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Surface ID:** CFG-09  
**Screen name:** Contract Values  
**Status:** Revised v6 screen specification  
**Design principle:** Simple, complete, legally safe, implementation-ready  

---

## 1. Purpose

This screen allows the user to confirm the tender-specific contract values that will appear in the Special Conditions of Contract, contract schedules, and contract-facing appendices.

It is the final configuration step before the user runs the Readiness Check.

---

## 2. Single User Decision

> What tender-specific contract values and obligations must carry into the generated contract documents?

Everything on this screen must support that decision.

---

## 3. User-Facing Position

| Item | Value |
|---|---|
| Dashboard location | Tender Management → Tender Configurations |
| Parent surface | UI-01 — Tender Configuration Home |
| Configuration step | CFG-09 |
| Previous step | CFG-08 — Forms & Evidence |
| Next action | Run Readiness Check |
| User-facing object | Tender Configuration |
| Source object | Approved Procurement Package |
| STD family context | Information Technology, for current implementation |

---

## 4. STD Grounding

This screen is grounded in **Part 3 — Contract** of the IT Standard Tender Document.

It covers tender-specific contract configuration for:

- Special Conditions of Contract;
- contract data values;
- delivery and implementation obligations carried forward from the tender configuration;
- support, warranty, maintenance, and service obligations;
- securities and guarantees where applicable;
- contract schedules and appendices generated from configured tender data.

The screen must not edit the locked General Conditions of Contract text. GCC text is rendered from the applicable Standard Tender Document. Tender-specific variation is configured through the SCC / Contract Values structure only.

---

## 5. Screen Ownership

| Area | Rule |
|---|---|
| Screen owns | Tender-specific contract values and contract-facing carry-forward decisions |
| Primary object | `TenderContractValueConfiguration` |
| Editable here | SCC values, contract data values, carry-forward confirmation, contract schedule labels, contract-facing obligation text where allowed |
| Read-only references | Tender Profile, TDS, IT Requirements, Implementation Schedule, System Inventory & Bidder Background, Price Schedule, Forms & Evidence |
| Must not own | GCC text, post-award contract administration, inspection execution, payment certification, contract variations, actual delivery status, award decision |

---

## 6. What This Screen Must Do

The screen must help the user:

1. Review tender-specific contract values.
2. Confirm values derived from earlier configuration steps.
3. Add missing SCC / contract data values.
4. Decide which configured obligations carry into contract documents.
5. Identify contract values that need attention before Readiness Check.
6. Keep post-award administration out of this tender-configuration workflow.

---

## 7. What This Screen Must Not Do

Do not include:

- editable GCC clauses;
- legal clause tree browsing;
- clause hashes, source anchors, rule IDs, schema versions, or binding IDs;
- award decision content;
- contract signing workflow;
- contract execution records;
- inspection and acceptance execution;
- payment certificates;
- contract variation/change-order processing;
- supplier performance management;
- actual delivery progress.

---

## 8. Default Layout

### 8.1 Page Header

Title:

```text
Contract Values
```

Subtitle:

```text
Confirm the tender-specific contract values and obligations that will appear in the contract documents.
```

Primary actions:

```text
Save Contract Values
Run Check
```

Do not use:

```text
Contract Administration
Contract Management
SCC Engine
Legal Clause Editor
GCC/SCC Control Center
```

---

### 8.2 Context Strip

Show only:

| Field | Example |
|---|---|
| Configuration Ref | TC-2026-0041 |
| Procurement Package Ref | PP-ICT-2026-009 |
| Tender Title | Data Center Hardware Refresh |
| STD Family | Information Technology |
| Procuring Entity | National Treasury |
| Procurement Method | Open National Tender |
| Wizard State | In Progress |
| Issues | 1 Blocker / 2 Warnings |

Do not show internal binding identifiers, hashes, schema versions, or package codes.

---

### 8.3 Guidance Panel

Title:

```text
Contract Values Guidance
```

Body:

```text
Use this screen to confirm the values and obligations that will appear in the contract documents. Values may come from the Tender Data Sheet, IT Requirements, Implementation Schedule, Price Schedule, or Forms & Evidence. Edit only the contract-specific values allowed for this tender configuration.
```

Boundary note:

```text
This screen prepares contract documents. It does not manage the signed contract after award.
```

---

## 9. Main Table

Use one table with tabs or filters for clarity.

Recommended tabs:

```text
All Contract Values
SCC Values
Delivery Obligations
Support & Warranty
Securities & Guarantees
Contract Schedules
Needs Attention
```

Table columns:

| Column | Required | Example |
|---|---:|---|
| Item | Yes | Performance Security |
| Category | Yes | Securities & Guarantees |
| Source | Yes | Tender Data Sheet |
| Contract Location | Yes | SCC / Contract Data |
| Value / Obligation | Yes | 10% of contract price |
| Status | Yes | Complete |
| Action | Yes | Edit |

Do not include scoring, price evaluation, actual supplier submissions, contract execution status, or post-award activity.

---

## 10. Approved Categories

Use only these categories:

| Category | Meaning |
|---|---|
| SCC Value | A tender-specific value that completes the Special Conditions of Contract or contract data |
| Delivery Obligation | A delivery or implementation obligation carried forward from requirements or schedule |
| Support & Warranty | Support, maintenance, warranty, service-level, or handover obligation |
| Security & Compliance Obligation | Security, privacy, confidentiality, residency, or compliance obligation carried into contract documents |
| Securities & Guarantees | Performance security, advance payment security, retention, or related guarantee setting |
| Contract Schedule | Contract appendix, schedule, attachment, or generated annex |
| Acceptance & Handover | Contract-facing acceptance, testing, handover, or completion condition |

---

## 11. Status Labels

Use only these labels:

| Status | Meaning |
|---|---|
| Complete | Required contract value is present and can be used in generated documents |
| Needs attention | Required value is missing, inconsistent, or needs user review |
| Review before handoff | Value is present but should be reviewed before Readiness Check passes |
| Not applicable | The value is not required for this tender configuration |

Do not use:

```text
Locked
Ready
Valid
Enabled
Approved
Executed
Signed
```

---

## 12. Sample Rows

| Item | Category | Source | Contract Location | Value / Obligation | Status | Action |
|---|---|---|---|---|---|---|
| Performance Security | Securities & Guarantees | Tender Data Sheet | SCC / Contract Data | 10% of contract price | Complete | Edit |
| Delivery Period | SCC Value | Implementation Schedule | SCC / Delivery Schedule | 6 months from notice to proceed | Complete | Edit |
| On-site Support | Support & Warranty | IT Requirements | Contract Schedule: Support | 3 years next-business-day on-site support | Complete | Edit |
| Data Residency | Security & Compliance Obligation | IT Requirements | Contract Schedule: Security | Production data must remain in Kenya unless otherwise approved | Review before handoff | Review |
| Acceptance Testing | Acceptance & Handover | Implementation Schedule | Contract Schedule: Acceptance | User acceptance testing required before final acceptance | Complete | Edit |
| Advance Payment Security | Securities & Guarantees | Tender Data Sheet | SCC / Contract Data | Not applicable | Not applicable | Review |
| Contract Attachments | Contract Schedule | Forms & Evidence | Contract Appendices | Missing required attachment list | Needs attention | Fix |

---

## 13. Drawer Behavior

A drawer opens when the user selects a row.

Drawer title:

```text
Edit Contract Value
```

Drawer sections:

### Section A — Contract Value

Fields:

| Field | Required | Editable | Notes |
|---|---:|---:|---|
| Item name | Yes | No for generated items; Yes for user-added items | Example: Performance Security |
| Category | Yes | Yes where allowed | Use approved categories only |
| Contract location | Yes | Yes where allowed | Example: SCC / Contract Data |
| Value / obligation text | Yes | Yes where allowed | User-facing contract value |
| Not applicable | Optional | Yes where allowed | Requires reason |

### Section B — Source

Fields:

| Field | Required | Editable | Notes |
|---|---:|---:|---|
| Source screen | Yes | No | Example: Tender Data Sheet |
| Source item | Optional | No | Example: Performance Security Requirement |
| Source value | Optional | No | Show only if useful |

### Section C — Review Notes

Fields:

| Field | Required | Editable | Notes |
|---|---:|---:|---|
| Review note | Optional | Yes | Internal note, not bidder-facing unless explicitly marked |
| Issue status | Yes | No | Derived from validation |

Drawer actions:

```text
Save Contract Value
Cancel
```

If the value is sourced from another screen and not editable here, show:

```text
This value is controlled by [Source Screen]. Edit it there.
```

Button:

```text
Open Source Step
```

---

## 14. Source Rules

Values may come from earlier configuration steps, but this screen must never make them feel magical.

Every row must show a source:

| Source | Example |
|---|---|
| Tender Data Sheet | Performance security requirement |
| IT Requirements | Support and warranty obligation |
| Implementation Schedule | Delivery period and acceptance checkpoints |
| System Inventory & Bidder Background | Site/location context carried into contract schedules |
| Price Schedule | Pricing schedule attachment reference |
| Forms & Evidence | Contract attachments and declarations |
| User entered | Additional permitted contract value |
| Standard Tender Document | Default contract structure or locked text reference |

If source is missing, show:

```text
Source not set
```

and mark row as:

```text
Needs attention
```

---

## 15. Downstream Impact

This screen feeds:

- Readiness Check;
- generated tender document;
- contract document preview;
- publication package;
- Tender Management handoff after publication readiness.

This screen affects generated contract documents, but it must not perform contract administration.

---

## 16. Readiness Behavior

The screen may show only summary-level readiness:

```text
1 Blocker / 2 Warnings
```

Allowed issue examples:

```text
Performance security value is missing.
Contract attachment list is incomplete.
Data residency obligation should be reviewed before handoff.
```

Forbidden issue examples:

```text
RULE_CONTRACT_009 failed
SCC_HASH_MISMATCH
CONTRACT_SCHEMA_NODE_INVALID
```

Detailed diagnostics belong in system/admin views, not this screen.

---

## 17. Empty State

If no contract values have been configured:

Title:

```text
No contract values configured yet
```

Body:

```text
Contract values are prepared from earlier configuration steps such as the Tender Data Sheet, IT Requirements, Implementation Schedule, Price Schedule, and Forms & Evidence. Run Check to identify the values that still need confirmation.
```

Actions:

```text
Run Check
Return to Configuration Home
```

---

## 18. Stitch Prompt

```text
Design CFG-09 — Contract Values for the KenTender Tender Configurations module.

Purpose:
Confirm the tender-specific contract values and obligations that will appear in the contract documents.

Single user decision:
What tender-specific contract values and obligations must carry into the generated contract documents?

Keep the screen simple and procurement-facing. This is not a contract administration screen.

Use this layout:
1. Page title: Contract Values.
2. Subtitle: Confirm the tender-specific contract values and obligations that will appear in the contract documents.
3. Context strip with only Configuration Ref, Procurement Package Ref, Tender Title, STD Family, Procuring Entity, Procurement Method, Wizard State, and Issues.
4. Guidance panel titled Contract Values Guidance.
5. Main table with tabs: All Contract Values, SCC Values, Delivery Obligations, Support & Warranty, Securities & Guarantees, Contract Schedules, Needs Attention.
6. Table columns: Item, Category, Source, Contract Location, Value / Obligation, Status, Action.
7. Detail drawer titled Edit Contract Value.
8. Sticky footer with Save Contract Values and Run Check.

Use only these status labels:
- Complete
- Needs attention
- Review before handoff
- Not applicable

Use only these categories:
- SCC Value
- Delivery Obligation
- Support & Warranty
- Security & Compliance Obligation
- Securities & Guarantees
- Contract Schedule
- Acceptance & Handover

Sample rows:
- Performance Security | Securities & Guarantees | Tender Data Sheet | SCC / Contract Data | 10% of contract price | Complete | Edit
- Delivery Period | SCC Value | Implementation Schedule | SCC / Delivery Schedule | 6 months from notice to proceed | Complete | Edit
- On-site Support | Support & Warranty | IT Requirements | Contract Schedule: Support | 3 years next-business-day on-site support | Complete | Edit
- Data Residency | Security & Compliance Obligation | IT Requirements | Contract Schedule: Security | Production data must remain in Kenya unless otherwise approved | Review before handoff | Review
- Contract Attachments | Contract Schedule | Forms & Evidence | Contract Appendices | Missing required attachment list | Needs attention | Fix

Do not show GCC clause editing, legal clause trees, source hashes, rule IDs, schema versions, award decisions, contract signing, inspection execution, payment certificates, contract variations, or supplier performance management.

Use procurement-facing language only.
```

---

## 19. Cursor Prompt

```text
Implement CFG-09 — Contract Values for the KenTender Tender Configurations module.

Screen purpose:
Confirm tender-specific contract values and obligations that will appear in generated contract documents.

Primary object:
TenderContractValueConfiguration

Required API shape:
{
  configuration_id,
  configuration_ref,
  procurement_package_ref,
  tender_title,
  std_family_label,
  procuring_entity_name,
  procurement_method_label,
  wizard_state_label,
  blocker_count,
  warning_count,
  tabs: [
    "All Contract Values",
    "SCC Values",
    "Delivery Obligations",
    "Support & Warranty",
    "Securities & Guarantees",
    "Contract Schedules",
    "Needs Attention"
  ],
  contract_values: [
    {
      contract_value_id,
      item_label,
      category,
      source_screen,
      source_item_label,
      contract_location,
      value_or_obligation,
      status,
      status_label,
      editable_here,
      read_only_reason,
      source_route,
      issue_count,
      action_label
    }
  ]
}

Render:
1. Page title: Contract Values.
2. Subtitle exactly: Confirm the tender-specific contract values and obligations that will appear in the contract documents.
3. Context strip with Configuration Ref, Procurement Package Ref, Tender Title, STD Family, Procuring Entity, Procurement Method, Wizard State, Issues.
4. Guidance panel.
5. Table columns: Item, Category, Source, Contract Location, Value / Obligation, Status, Action.
6. Drawer for editing one contract value.
7. Footer actions: Save Contract Values, Run Check.

Rules:
- Do not render editable GCC text.
- Do not render contract administration, signing, delivery execution, inspection execution, payment certification, or variation management.
- Every row must show a source.
- If a value is owned by another screen, show read-only value with Open Source Step.
- Do not use internal terms such as binding, instance, hash, schema node, package code, or rule ID.
- Use human-readable status labels only.
- Do not hardcode realistic data outside approved seed fixtures.

Acceptance criteria:
- User can identify missing contract values quickly.
- User can see where each value came from.
- User can edit only values owned by this screen.
- User can navigate to source steps for values owned elsewhere.
- The screen does not look like post-award contract management.
```

---

## 20. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User understands they are confirming contract values, not managing a signed contract |
| STD grounding | Screen covers SCC / contract-facing values and does not edit GCC text |
| Ownership clarity | Contract values are owned here; source data is referenced only |
| No magical values | Every value shows a source |
| Simplicity | Main table uses only contract value rows, not clause trees or admin metadata |
| Downstream awareness | Screen feeds Readiness Check and generated contract documents |
| Boundary protection | No award, signing, inspection, payment, variation, or performance management appears |
| Implementation clarity | Stitch and Cursor receive exact labels, columns, categories, statuses, sample rows, and prompts |

---

## 21. Final Rule

If a field does not help the user confirm tender-specific contract values for generated contract documents, remove it from CFG-09.
