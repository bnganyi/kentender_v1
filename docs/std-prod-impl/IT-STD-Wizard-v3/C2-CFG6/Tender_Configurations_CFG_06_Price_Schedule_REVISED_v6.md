# Tender Configurations — CFG-06 Price Schedule v6

**Project:** KenTender e-Procurement System  
**Module:** Tender Configurations  
**Configuration family:** Information Technology STD  
**Screen ID:** CFG-06  
**Screen name:** Price Schedule  
**Status:** Revised v6 specification  
**Design rule:** Simple, user-facing, STD-grounded, implementation-ready  

---

## 1. Canonical Position

| Item | Value |
|---|---|
| User-facing area | Tender Management → Tender Configurations |
| Parent surface | UI-01 — Tender Configuration Home |
| Configuration step | CFG-06 |
| Comes after | CFG-05 — System Inventory & Bidder Background |
| Comes before | CFG-07 — Evaluation Setup |
| Lifecycle stage | Configuration |
| Primary object | Tender price schedule configuration |
| User-facing object | Price Schedule |
| STD family | Information Technology |
| Primary STD anchor | Section IV price schedule forms, especially supply/install and recurrent cost pricing; informed by Section VIII System Inventory Tables |
| Workflow gate? | No. This is a configuration step. |

---

## 2. User Goal

Allow the procurement user to define **how bidders must price the IT tender**.

---

## 3. Single User Decision

> How should bidders break down and submit their prices?

Everything on this screen must support that decision.

---

## 4. Screen Ownership

| Area | Rule |
|---|---|
| This screen owns | Price schedule sections, price items, pricing basis, quantities, units, duration, mandatory/optional treatment, currency/tax instruction, evaluated-price inclusion, bidder pricing instructions |
| This screen references | Tender Profile, TDS currency/tax settings, IT Requirements, Implementation Schedule, System Inventory & Bidder Background |
| This screen does not own | Technical requirement wording, implementation milestones, inventory/background descriptions, evaluation scores, bidder-submitted prices, contract payment administration |
| Editable here | Price items and bidder pricing instructions |
| Read-only here | Source requirement, source inventory item, source milestone, currency if owned by TDS |
| Must not show | Actual bidder prices, evaluated bid rankings, budget approvals, payment certificates, contract payment execution, hidden formula/rule IDs |

---

## 5. STD Grounding

The IT STD includes price schedule forms under tendering forms and links IT pricing to the system being supplied, installed, implemented, supported, or recurrently maintained.

This screen must support at least two price groupings:

1. **Supply and Installation Items** — one-time supply, installation, configuration, commissioning, training, migration, and implementation-related prices.
2. **Recurrent Cost Items** — recurring licenses, subscriptions, hosting, maintenance, support, warranty extensions, managed services, and other ongoing costs.

The screen may reference System Inventory and Implementation Schedule, but it must not become an inventory or project-delivery screen.

---

## 6. Downstream Impact

This screen feeds:

| Downstream area | How it uses this screen |
|---|---|
| Evaluation Setup | Defines the financial evaluation structure and which price items are included in evaluated price |
| Forms & Evidence | Determines bidder price forms and required price schedule completion |
| Contract Values | Carries accepted price structure into contract schedules where applicable |
| Tender Preview | Renders bidder-facing price schedules |
| Readiness Check | Verifies required price items, units, quantities, and instructions are complete |

This screen must not configure actual financial evaluation scoring or award comparison. It only defines the price submission structure.

---

## 7. Layout

### 7.1 Page Header

Title:

```text
Price Schedule
```

Subtitle:

```text
Define how bidders must price the tender.
```

Primary actions:

```text
Add Price Item
Import Price Items
Run Check
```

Footer actions:

```text
Save Price Schedule
Continue to Evaluation Setup
```

`Continue to Evaluation Setup` is disabled while blocker issues remain.

---

### 7.2 Context Strip

Show only:

| Field | Example |
|---|---|
| Procurement Package Ref | PP-ICT-2024-009 |
| Tender Title | Data Center Hardware Refresh |
| Procuring Entity | National Treasury |
| Procurement Method | Open National Tender |
| STD Family | Information Technology |
| Standard Tender Document | IT Standard Tender Document — April 2022 |
| Wizard State | In Progress |
| Issues | 0 Blockers / 2 Warnings |

Do not show internal IDs, hashes, schema versions, binding IDs, or source anchors.

---

### 7.3 Section Tabs

Use these tabs:

```text
All Price Items
Supply & Installation
Recurrent Costs
Optional / Provisional Items
Needs Attention
```

Tab meanings:

| Tab | Meaning |
|---|---|
| All Price Items | Every configured price item |
| Supply & Installation | One-time supply, installation, configuration, commissioning, implementation, training, migration |
| Recurrent Costs | Recurring support, maintenance, subscriptions, licenses, hosting, managed services |
| Optional / Provisional Items | Items bidders may price separately or items not included in the evaluated price unless expressly configured |
| Needs Attention | Items missing required pricing instructions, quantity/unit, duration, or evaluated-price decision |

---

## 8. Main Table

Use this exact table structure:

| Column | Purpose |
|---|---|
| Item ID | Short generated identifier, e.g. `PRI-001` |
| Price Item | User-facing item name |
| Price Group | Supply & Installation / Recurrent Cost / Optional / Provisional |
| Pricing Basis | Unit price / Lump sum / Monthly / Annual / Per user / Per site / Per milestone / As specified |
| Quantity / Duration | Quantity, period, or basis bidders must price against |
| Source | Requirement / Inventory / Schedule / User added |
| Evaluated Price | Included / Excluded / Conditional |
| Status | Complete / Needs attention |
| Action | Edit / Fix / Review |

### Sample rows

| Item ID | Price Item | Price Group | Pricing Basis | Quantity / Duration | Source | Evaluated Price | Status | Action |
|---|---|---|---|---|---|---|---|---|
| PRI-001 | Server compute nodes | Supply & Installation | Unit price | 12 units | System Inventory | Included | Complete | Edit |
| PRI-002 | Installation and commissioning | Supply & Installation | Lump sum | 1 lot | Implementation Schedule | Included | Complete | Edit |
| PRI-003 | Data migration support | Supply & Installation | Lump sum | 1 migration workstream | IT Requirements | Included | Complete | Edit |
| PRI-004 | Annual hardware maintenance | Recurrent Cost | Annual | 3 years | IT Requirements | Included | Complete | Edit |
| PRI-005 | Cloud backup subscription | Recurrent Cost | Monthly | 36 months | IT Requirements | Conditional | Needs attention | Fix |
| PRI-006 | Optional additional storage shelf | Optional / Provisional | Unit price | Quantity to be stated by bidder | User added | Excluded | Complete | Review |

---

## 9. Required Status Labels

Use only:

| Status | Meaning |
|---|---|
| Complete | Required pricing structure is sufficiently defined |
| Needs attention | One or more required pricing details are missing or inconsistent |

Do not use:

```text
Valid
Invalid
Ready
Locked
Passed
Failed
```

---

## 10. Price Group Definitions

| Price group | Exact description |
|---|---|
| Supply & Installation | One-time prices for items or services supplied, installed, configured, commissioned, migrated, trained, or handed over under the tender. |
| Recurrent Cost | Ongoing prices for licenses, subscriptions, hosting, support, maintenance, warranty extensions, managed services, or other recurring obligations. |
| Optional / Provisional | Separately priced items that may be optional, provisional, conditional, or excluded from evaluated price unless explicitly included. |

---

## 11. Pricing Basis Options

Use only these labels unless family-specific rules add more:

```text
Unit price
Lump sum
Monthly
Annual
Per user
Per site
Per device
Per milestone
As specified
```

---

## 12. Evaluated Price Options

Use these labels:

| Label | Meaning |
|---|---|
| Included | The item forms part of the evaluated financial price. |
| Excluded | The item is priced for information or optional use but is not included in evaluated financial price. |
| Conditional | Inclusion depends on a stated tender rule or option. |

Do not calculate bidder rankings on this screen.

---

## 13. Price Item Drawer

Open when the user selects `Add Price Item`, `Edit`, or `Fix`.

### Drawer title

For new item:

```text
Add Price Item
```

For existing item:

```text
Edit Price Item
```

### Drawer sections and exact fields

#### A. Price Item

| Field | Control | Required | Notes |
|---|---|---:|---|
| Price Item Name | Text input | Yes | Example: `Server compute nodes` |
| Price Group | Select | Yes | Supply & Installation / Recurrent Cost / Optional / Provisional |
| Bidder-facing Description | Text area | Yes | Plain instruction shown to bidders |
| Source | Read-only or select | Yes | Requirement / Inventory / Schedule / User added |

#### B. Pricing Basis

| Field | Control | Required | Notes |
|---|---|---:|---|
| Pricing Basis | Select | Yes | Use approved pricing basis labels |
| Quantity | Number/text | Conditional | Required unless pricing basis is lump sum or as specified |
| Unit | Text/select | Conditional | Example: units, users, sites, months, years |
| Duration | Text/select | Conditional | Required for recurrent pricing |
| Currency | Read-only/select | Yes | Usually sourced from TDS |
| Tax Instruction | Text/select | Yes | Example: tax inclusive / tax exclusive / as specified in TDS |

#### C. Evaluated Price

| Field | Control | Required | Notes |
|---|---|---:|---|
| Evaluated Price Treatment | Select | Yes | Included / Excluded / Conditional |
| Conditional Rule | Text area | Conditional | Required when treatment is Conditional |
| Bidder Pricing Instruction | Text area | Yes | Exact instruction bidders will see |

#### D. References

Display only as references:

| Reference | Display rule |
|---|---|
| Related Requirement | Show title and `View requirement` link |
| Related Inventory Item | Show title and `View inventory item` link |
| Related Milestone | Show title and `View schedule` link |
| Evaluation Setup | Show `Financial evaluation configured in Evaluation Setup` |

Do not allow editing of requirements, inventory, schedule, or evaluation settings inside this drawer.

---

## 14. Empty State

If no price items exist, show:

```text
No price items have been configured yet.

Add the price items bidders must use to submit their financial proposal. You can add supply and installation items, recurrent cost items, and optional or provisional items.
```

Primary button:

```text
Add Price Item
```

Secondary button:

```text
Import Price Items
```

---

## 15. Import Behavior

`Import Price Items` may import suggested items from:

| Source | Behavior |
|---|---|
| System Inventory & Bidder Background | Suggest supply/install or recurrent cost items linked to inventory records |
| IT Requirements | Suggest price items for requirements that imply supply, implementation, support, licensing, or services |
| Implementation Schedule | Suggest implementation, commissioning, migration, training, or milestone-based services |
| Standard IT price template | Suggest standard IT price items |

Imported items are draft suggestions. The user must confirm price group, pricing basis, quantity/duration, evaluated-price treatment, and bidder instruction before the item is complete.

---

## 16. Validation Rules

### Blockers

| Rule | Message |
|---|---|
| Missing price item name | Add a price item name. |
| Missing price group | Select a price group. |
| Missing pricing basis | Select how bidders should price this item. |
| Missing quantity/unit where required | Enter the quantity and unit bidders must price against. |
| Missing recurrent duration | Enter the duration for this recurrent cost item. |
| Missing evaluated-price treatment | Choose whether this item is included in the evaluated price. |
| Conditional evaluated price without condition | Explain when this item is included in the evaluated price. |
| Missing bidder pricing instruction | Add the instruction bidders will see. |

### Warnings

| Rule | Message |
|---|---|
| Optional item included in evaluated price | Confirm that this optional item should be included in the evaluated price. |
| Inventory item not priced | Review whether this inventory item needs a price item. |
| Requirement may require pricing | Review whether this requirement needs a linked price item. |
| Recurrent item has short or unclear duration | Confirm the recurrent cost duration. |
| User-added item has no source link | Confirm this item is intentionally user-added. |

---

## 17. Completion Rule

The screen is complete when:

1. All required price items have a name, group, pricing basis, and bidder instruction.
2. All quantity/unit/duration fields required by the pricing basis are complete.
3. Every item has an evaluated-price treatment.
4. Conditional evaluated-price items have a clear condition.
5. There are no blocker findings.

Warnings may remain, but must be visible.

---

## 18. Forbidden Content

Do not show:

```text
Actual bidder-submitted prices
Bid rankings
Financial evaluation scores
Award recommendation
Budget approval workflow
Payment certificates
Contract payment execution
Project delivery progress
Rule IDs
Schema names
Hash values
Internal binding IDs
```

---

## 19. Stitch Prompt

```text
Design CFG-06 — Price Schedule for the KenTender Tender Configurations module.

Screen purpose:
Define how bidders must price the tender.

Single user decision:
How should bidders break down and submit their prices?

Use this exact title:
Price Schedule

Use this exact subtitle:
Define how bidders must price the tender.

The screen is part of one tender configuration. It is not a bid evaluation screen, budget screen, contract payment screen, or procurement accounting screen.

Top context strip must show only:
- Procurement Package Ref
- Tender Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document
- Wizard State
- Issues

Primary actions:
- Add Price Item
- Import Price Items
- Run Check

Main tabs:
- All Price Items
- Supply & Installation
- Recurrent Costs
- Optional / Provisional Items
- Needs Attention

Main table columns:
- Item ID
- Price Item
- Price Group
- Pricing Basis
- Quantity / Duration
- Source
- Evaluated Price
- Status
- Action

Use these sample rows:
1. PRI-001 | Server compute nodes | Supply & Installation | Unit price | 12 units | System Inventory | Included | Complete | Edit
2. PRI-002 | Installation and commissioning | Supply & Installation | Lump sum | 1 lot | Implementation Schedule | Included | Complete | Edit
3. PRI-003 | Data migration support | Supply & Installation | Lump sum | 1 migration workstream | IT Requirements | Included | Complete | Edit
4. PRI-004 | Annual hardware maintenance | Recurrent Cost | Annual | 3 years | IT Requirements | Included | Complete | Edit
5. PRI-005 | Cloud backup subscription | Recurrent Cost | Monthly | 36 months | IT Requirements | Conditional | Needs attention | Fix
6. PRI-006 | Optional additional storage shelf | Optional / Provisional | Unit price | Quantity to be stated by bidder | User added | Excluded | Complete | Review

Status labels:
- Complete
- Needs attention

Do not use:
- Valid
- Invalid
- Ready
- Locked
- Passed
- Failed

Drawer:
Use a right-side drawer for Add/Edit/Fix.

Drawer sections:
1. Price Item
   - Price Item Name
   - Price Group
   - Bidder-facing Description
   - Source
2. Pricing Basis
   - Pricing Basis
   - Quantity
   - Unit
   - Duration
   - Currency
   - Tax Instruction
3. Evaluated Price
   - Evaluated Price Treatment
   - Conditional Rule
   - Bidder Pricing Instruction
4. References
   - Related Requirement
   - Related Inventory Item
   - Related Milestone
   - Evaluation Setup note

The drawer must not allow editing of requirements, inventory, schedule, or evaluation settings.

Footer actions:
- Save Price Schedule
- Continue to Evaluation Setup

Disable Continue to Evaluation Setup if blocker issues remain.

Do not show actual bidder prices, bid rankings, financial evaluation scores, award recommendations, budget approvals, payment certificates, contract payment execution, project delivery progress, rule IDs, hashes, schemas, or internal binding IDs.
```

---

## 20. Cursor Prompt

```text
Implement CFG-06 — Price Schedule for the KenTender Tender Configurations module.

Use the mounted UI bundle / Frappe Desk page architecture. Do not use a raw Stitch iframe. Do not load Tailwind from CDN.

Screen goal:
Define how bidders must price the tender.

Primary object:
TenderConfigurationPriceSchedule

API shape:
{
  configuration_id,
  procurement_package_ref,
  tender_title,
  procuring_entity_name,
  procurement_method_label,
  std_family_label,
  standard_tender_document_label,
  wizard_state_label,
  blocker_count,
  warning_count,
  active_tab,
  price_items: [
    {
      item_id,
      item_name,
      price_group,
      price_group_label,
      pricing_basis,
      pricing_basis_label,
      quantity_display,
      source_type,
      source_label,
      evaluated_price_treatment,
      evaluated_price_treatment_label,
      status,
      status_label,
      action_label,
      route_or_drawer_action
    }
  ],
  summary: {
    total_items,
    supply_installation_count,
    recurrent_cost_count,
    optional_provisional_count,
    needs_attention_count
  }
}

Allowed tabs:
- all_price_items
- supply_installation
- recurrent_costs
- optional_provisional
- needs_attention

Allowed status labels:
- Complete
- Needs attention

Allowed price groups:
- Supply & Installation
- Recurrent Cost
- Optional / Provisional

Allowed pricing basis labels:
- Unit price
- Lump sum
- Monthly
- Annual
- Per user
- Per site
- Per device
- Per milestone
- As specified

Allowed evaluated price labels:
- Included
- Excluded
- Conditional

Render:
1. Page title: Price Schedule.
2. Subtitle: Define how bidders must price the tender.
3. Context strip with only the specified fields.
4. Primary actions: Add Price Item, Import Price Items, Run Check.
5. Tabs listed above.
6. Main table with exact columns:
   Item ID, Price Item, Price Group, Pricing Basis, Quantity / Duration, Source, Evaluated Price, Status, Action.
7. Right drawer for Add/Edit/Fix with sections:
   Price Item, Pricing Basis, Evaluated Price, References.
8. Footer actions:
   Save Price Schedule, Continue to Evaluation Setup.
9. Disable Continue to Evaluation Setup if blocker_count > 0.

Rules:
- Do not render actual bidder prices.
- Do not render bid rankings.
- Do not render financial evaluation scores.
- Do not render award recommendation.
- Do not render budget approval or payment workflow.
- Do not edit IT Requirements, System Inventory, Implementation Schedule, or Evaluation Setup inside this screen.
- References to requirements, inventory, milestones, and evaluation must be read-only links.
- No hardcoded realistic values outside approved seed/demo fixtures.
- Use procurement-facing language only.
- Do not show internal IDs, hashes, schema versions, rule IDs, or binding IDs.

Acceptance criteria:
- User can understand how bidders will price the tender without seeing evaluation or contract-payment concepts.
- User can add/edit/fix price items from a drawer.
- Every price item has a clear group, pricing basis, quantity/duration, source, evaluated-price treatment, and bidder instruction.
- Continue to Evaluation Setup is blocked only by blocker findings.
- Screen remains focused on bidder price submission structure.
```

---

## 21. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell the screen defines how bidders submit prices. |
| STD grounding | Screen covers supply/install and recurrent cost pricing for IT STD. |
| Ownership | Screen owns pricing structure only. |
| No evaluation leakage | Screen does not show scores, bid rankings, award recommendation, or actual bidder prices. |
| No payment leakage | Screen does not show budget approval, payment certificates, or contract payment execution. |
| Table clarity | Table includes Price Group, Pricing Basis, Quantity / Duration, Source, Evaluated Price, Status, and Action. |
| Drawer clarity | Drawer edits price items only and shows references as read-only links. |
| Status simplicity | Only Complete and Needs attention are used. |
| Continuation rule | Continue to Evaluation Setup is disabled while blocker issues remain. |
| Implementation readiness | Stitch and Cursor prompts contain exact labels, rows, statuses, and forbidden content. |

---

## 22. Final Rule

If a field does not help the user define how bidders must price the tender, remove it from CFG-06.
