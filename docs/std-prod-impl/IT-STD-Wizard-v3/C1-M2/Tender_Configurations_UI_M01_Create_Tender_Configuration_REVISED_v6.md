# UI-M01 — Create Tender Configuration

**Project:** KenTender e-Procurement System  
**Area:** Tender Management  
**Menu location:** Tender Management → Tender Configurations  
**Surface type:** Modal opened from UI-00 — Tender Configurations Dashboard  
**Status:** Revised v6  
**Design rule:** procurement-package intake; generic across STD families; no internal architecture terms

---

## 1. Purpose

Create a tender configuration from an approved procurement package that does not already have an active configuration.

This modal exists because the dashboard has two object types:

| Dashboard area | Object type | Modal role |
|---|---|---|
| Ready to Configure | Approved Procurement Package | Create a new tender configuration from the selected package |
| Other tabs | Existing Tender Configuration | Not used; user opens or continues the existing configuration |

---

## 2. Single user decision

> Which approved procurement package should be used to create a tender configuration?

Everything in this modal must support that decision.

---

## 3. Lifecycle position

```text
Approved Procurement Package
→ Create Tender Configuration
→ Tender Configuration Home
→ Configure tender-specific information
→ Readiness Check
→ Review
→ Tender Document Preview
→ Publication Handoff
→ Tender Management publication workflow
```

This modal does **not** publish a tender, create a bid window, notify suppliers, start evaluation, approve the configuration, or create a contract.

---

## 4. User-facing terminology

Use these terms:

| Concept | User-facing label |
|---|---|
| Upstream planning handoff | Approved Procurement Package |
| New workspace created by the modal | Tender Configuration |
| Standard document family | STD Family |
| Specific standard document | Standard Tender Document |
| Upstream planning reference | Planning Package Ref |

Do **not** show these terms in the procurement-user UI:

```text
Tender Shell
TenderSTDInstance
STD binding
binding ID
STD package code
schema version
hash
configuration object
```

---

## 5. Entry modes

The modal may open in two ways.

### Entry mode A — From primary dashboard action

User clicks:

```text
Create Tender Configuration
```

Behavior:

- Modal opens with no package preselected.
- User must select an eligible approved procurement package.
- Package selector is visible and editable.

### Entry mode B — From a Ready to Configure row

User clicks:

```text
Create Configuration
```

on a specific approved procurement package row.

Behavior:

- Modal opens with that package preselected.
- Package selector remains visible but may be changed if policy allows.
- Read-only context fields are populated immediately.

Do not open this modal from In Progress, Needs Attention, Ready for Review, Ready for Publication, or Completed rows. Those rows already represent tender configurations and should open the existing configuration.

---

## 6. Modal title and helper text

### Modal title

```text
Create Tender Configuration
```

### Helper text

```text
Select an approved procurement package. KenTender will create a tender configuration using the applicable Standard Tender Document.
```

Keep this helper text exactly. Do not mention tender shells, bindings, instances, package codes, hashes, or schema versions.

---

## 7. Fields

### Editable field

| Field | Control | Required | Exact label | Exact helper text |
|---|---|---:|---|---|
| Approved Procurement Package | Searchable select | Yes | `Approved Procurement Package` | `Choose the approved package that needs a tender configuration.` |

Option label format:

```text
[Planning Package Ref] — [Procurement Title] · [STD Family]
```

Example:

```text
PP-ICT-2024-009 — Data Center Hardware Refresh · Information Technology
```

The selector must list only packages that are:

- approved;
- eligible for tender configuration;
- not already linked to an active tender configuration;
- visible to the current user.

### Read-only context fields after package selection

| Exact label | Example | Source |
|---|---|---|
| `Planning Package Ref` | `PP-ICT-2024-009` | Approved procurement package |
| `Procurement Title` | `Data Center Hardware Refresh` | Approved procurement package |
| `Procuring Entity` | `National Treasury` | Approved procurement package |
| `Procurement Method` | `Open National Tender` | Approved procurement package |
| `STD Family` | `Information Technology` | Derived from package/category/STD rules |
| `Standard Tender Document` | `IT Standard Tender Document — April 2022` | Applicable active STD version |

If no package is selected, each read-only field must show:

```text
Select a package first
```

Do not show blank values, mock values, hashes, IDs, or technical metadata.

---

## 8. Standard Tender Document rule

Default behavior:

```text
KenTender selects the applicable active Standard Tender Document from the selected procurement package and STD family rules.
```

The Standard Tender Document field is read-only by default.

Manual selection is allowed only when all are true:

1. More than one active Standard Tender Document is valid for the selected package.
2. The user has permission to choose the document version.
3. No tender configuration has yet been created for the package.

If manual selection is allowed, use:

| Field | Exact label | Helper text |
|---|---|---|
| Standard Tender Document | `Standard Tender Document` | `Choose the approved standard document to use for this configuration.` |

Do not expose STD version hashes, rule IDs, schema versions, binding IDs, or import package codes.

---

## 9. Actions

| Button | Behavior |
|---|---|
| `Cancel` | Closes the modal without creating anything. |
| `Create Configuration` | Creates a new tender configuration and opens its Tender Configuration Home. |

Enable `Create Configuration` only when:

- an approved procurement package is selected;
- the package is eligible;
- no active configuration already exists for the package;
- the applicable Standard Tender Document is resolved;
- the user has create permission.

Do not use these button labels:

```text
Start Configuration
Create Tender
Create Tender Shell
Bind STD
Continue
```

---

## 10. Validation and error messages

Use calm, user-facing messages.

| Condition | Message |
|---|---|
| No package selected | `Select an approved procurement package before creating a configuration.` |
| Package already has active configuration | `This procurement package already has a tender configuration. Open the existing configuration instead.` |
| Package is not approved | `Only approved procurement packages can be used to create a tender configuration.` |
| No applicable STD found | `No active Standard Tender Document is available for this procurement package. Contact the STD administrator.` |
| User lacks permission | `You do not have permission to create a tender configuration for this package.` |
| Package no longer eligible | `This procurement package is no longer eligible for configuration. Refresh the dashboard and try again.` |

No raw backend exception should be shown to the user.

---

## 11. Success behavior

After successful creation:

1. Close the modal.
2. Show toast:

```text
Tender configuration created.
```

3. Navigate to:

```text
UI-01 — Tender Configuration Home
```

for the newly created configuration.

Do not navigate directly to Tender Data Sheet, IT Requirements, System Inventory, or any family-specific configuration step.

---

## 12. API contract

### Eligible package list

```http
GET /api/method/kentender_procurement.tender_configurations.get_eligible_procurement_packages
```

Response:

```json
{
  "packages": [
    {
      "package_id": "PKG-0001",
      "planning_package_ref": "PP-ICT-2024-009",
      "procurement_title": "Data Center Hardware Refresh",
      "procuring_entity_name": "National Treasury",
      "procurement_method_label": "Open National Tender",
      "std_family_key": "IT",
      "std_family_label": "Information Technology",
      "applicable_std_document_id": "STD-IT-2022-04",
      "applicable_std_document_label": "IT Standard Tender Document — April 2022",
      "can_create_configuration": true,
      "ineligibility_reason": null
    }
  ]
}
```

### Create configuration

```http
POST /api/method/kentender_procurement.tender_configurations.create_tender_configuration
```

Request:

```json
{
  "package_id": "PKG-0001",
  "std_document_id": "STD-IT-2022-04"
}
```

Response:

```json
{
  "configuration_id": "TCFG-0001",
  "configuration_ref": "TCFG-ICT-2024-009",
  "std_family_key": "IT",
  "std_family_label": "Information Technology",
  "redirect_route": "/desk/tender-configuration-home?configuration_id=TCFG-0001"
}
```

Internal IDs may be used in API payloads and routing. They must not replace user-facing labels in the modal.

---

## 13. Stitch prompt

```text
Design a KenTender modal titled "Create Tender Configuration".

The modal opens from the Tender Configurations Dashboard under Tender Management.

User goal:
Create a tender configuration from an approved procurement package.

Single user decision:
Which approved procurement package should be used to create a tender configuration?

Use exactly this helper text:
"Select an approved procurement package. KenTender will create a tender configuration using the applicable Standard Tender Document."

Fields:
1. Approved Procurement Package — searchable select.
   Helper text: "Choose the approved package that needs a tender configuration."
   Option format: "PP-ICT-2024-009 — Data Center Hardware Refresh · Information Technology"

After a package is selected, show these read-only context fields:
- Planning Package Ref
- Procurement Title
- Procuring Entity
- Procurement Method
- STD Family
- Standard Tender Document

If no package is selected, each read-only field should show "Select a package first".

Buttons:
- Cancel
- Create Configuration

"Create Configuration" is disabled until the package is selected, eligible, and the applicable Standard Tender Document is resolved.

Do not show or mention:
Tender Shell, TenderSTDInstance, STD binding, binding ID, STD package code, schema version, hash, configuration object, tender record, publication, bid window, or evaluation.

Visual style:
Professional government workflow modal. Simple, calm, procurement-facing. No technical metadata, no legal clause details, no dashboard table inside the modal.
```

---

## 14. Cursor prompt

```text
Implement UI-M01 — Create Tender Configuration as a modal opened from UI-00 — Tender Configurations Dashboard.

Purpose:
Create a tender configuration from an approved procurement package.

Important object model:
- The Ready to Configure dashboard tab shows approved procurement packages.
- This modal creates a tender configuration from one selected approved procurement package.
- Existing tender configuration rows must not open this modal; they open the existing configuration.

Forbidden visible UI terms:
- Tender Shell
- TenderSTDInstance
- STD binding
- binding ID
- STD package code
- schema version
- hash
- configuration object
- tender record

Required UI:
- Modal title: Create Tender Configuration
- Helper text: Select an approved procurement package. KenTender will create a tender configuration using the applicable Standard Tender Document.
- Searchable select label: Approved Procurement Package
- Select helper text: Choose the approved package that needs a tender configuration.
- Read-only context fields:
  - Planning Package Ref
  - Procurement Title
  - Procuring Entity
  - Procurement Method
  - STD Family
  - Standard Tender Document
- Buttons:
  - Cancel
  - Create Configuration

Behavior:
1. Fetch eligible packages from get_eligible_procurement_packages.
2. If opened from a Ready to Configure row, preselect that package.
3. Populate read-only context fields from the selected package.
4. Show "Select a package first" in read-only fields until a package is selected.
5. Enable Create Configuration only when can_create_configuration is true and an applicable Standard Tender Document is resolved.
6. On create, call create_tender_configuration.
7. On success, close modal, show toast "Tender configuration created.", and navigate to redirect_route.
8. If the package already has an active configuration, show "This procurement package already has a tender configuration. Open the existing configuration instead."
9. Do not create a published tender, publication record, bid window, evaluation record, or contract from this modal.
```

---

## 15. Acceptance checklist

| Test | Pass condition |
|---|---|
| Correct source object | Modal creates from an approved procurement package, not from a tender shell or tender record. |
| Dashboard consistency | Modal is used only for Ready to Configure package rows or the primary create action. |
| Duplicate prevention | Packages with active configurations cannot create duplicates. |
| STD family support | Modal works for IT, Works, Goods, Consultancy, and future STD families. |
| User-facing language | No forbidden internal terms are visible. |
| Simplicity | User selects one package and reviews clear read-only context. |
| Button behavior | `Create Configuration` is disabled until package and STD are valid. |
| Success routing | Success opens Tender Configuration Home, not a downstream configuration step. |
| Scope discipline | Modal does not publish, open bidding, start review, start evaluation, or create contracts. |

---

## 16. Final rule

If a field does not help the user select an approved procurement package and understand what tender configuration will be created, remove it from this modal.
