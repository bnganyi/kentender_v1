# IT Tender Wizard Screen 01 — IT Tender Configurations Dashboard

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 01 — IT Tender Configurations Dashboard  
**Status:** Revised UX specification  
**Design rule:** Work queue, not configuration model.

---

## 1. User Journey

A procurement user opens the IT Tender Wizard area to find or create an IT tender configuration.

The user should immediately understand:

1. Which IT tender configurations already exist.
2. Which configurations need attention.
3. Which approved procurement packages can start a new IT tender configuration.
4. Where to continue.

---

## 2. Single User Decision

> Which IT tender configuration should I open or create?

Everything on the screen must support that decision.

---

## 3. Lifecycle Position

This screen sits before configuration work begins or resumes.

```text
Approved Procurement Package
→ IT Tender Configuration
```

The screen must not use the term `Tender Shell`.

---

## 4. IT STD Grounding

This screen is not an IT STD content section.

It routes users to configurations based on the IT Standard Tender Document. It must not expose clause trees, hashes, STD package codes, schema versions, or render diagnostics.

---

## 5. Screen Ownership

| Item | Rule |
|---|---|
| Screen owns | Work queue, search/filter, create configuration entry point |
| Primary object | IT Tender Configuration list |
| Editable here | None |
| Main actions | Create IT Tender Configuration, Continue, Fix, Review |
| Read-only references | Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, Issues, Last Updated |
| Must not own | Tender Profile fields, TDS values, requirements, schedule, inventory, pricing, evaluation, evidence, SCC values, approval decision, publication |

---

## 6. Default Layout

### Page title

```text
IT Tender Configurations
```

### Subtitle

```text
Create or continue IT tender configurations from approved procurement packages.
```

### Primary action

```text
Create IT Tender Configuration
```

---

## 7. Dashboard Table

Show these columns only:

| Column | Exact display rule |
|---|---|
| Tender Ref | Show tender reference if already assigned; otherwise show `Not assigned yet` |
| Tender Title | Show tender title from the approved procurement package or Tender Profile |
| Planning Package Ref | Show the approved procurement package reference |
| Procuring Entity | Show procuring entity name |
| Procurement Method | Show user-facing method label, for example `Open National Tender` |
| Status | Show wizard state as a plain label |
| Issues | Show `0 Blockers / 2 Warnings`, `Needs attention`, or blank |
| Last Updated | Show date/time and user where available |
| Action | Continue, Fix, Review, or Open |

Do not show `Tender Shell`, `TenderSTDInstance`, binding IDs, hashes, schema versions, source anchors, or package codes.

---

## 8. Status Labels

Use these dashboard labels:

| Label | Meaning |
|---|---|
| In configuration | User is still completing configuration steps |
| Needs attention | Blockers or returned corrections exist |
| Ready for validation | Required configuration appears complete enough to validate |
| Under review | Submitted for formal review |
| Approved for preview | Review approved; final preview can be generated or opened |
| Publication ready | Handoff to Tender Management is ready |

Do not use `Locked` or `Ready`.

---

## 9. Create IT Tender Configuration Modal

### Modal title

```text
Create IT Tender Configuration
```

### Helper text

```text
Select the approved procurement package that requires an IT tender configuration. The planning reference, procuring entity, procurement method, and applicable standard tender document will be filled from the package.
```

### Fields

| Field label | Behavior |
|---|---|
| Approved Procurement Package | Required selector |
| Planning Package Ref | Read-only after package selection |
| Procuring Entity | Read-only after package selection |
| Procurement Method | Read-only after package selection |
| Standard Tender Document | Read-only unless more than one valid IT STD version is available and the user has selection permission |

### Example selected package

```text
PP-ICT-2024-009 — Data Center Hardware Refresh
```

### Buttons

```text
Cancel
Create Configuration
```

### Forbidden modal terms

```text
Tender Shell
Tender to Configure
STD Package Code
TenderSTDInstance
STD binding
Start Configuration
```

---

## 10. Empty State

If there are no configurations:

```text
No IT tender configurations yet.
Create an IT tender configuration from an approved procurement package.
```

Primary button:

```text
Create IT Tender Configuration
```

---

## 11. Stitch Prompt

```text
Design Screen 01 for the KenTender IT Tender Configuration Wizard.

Screen name: IT Tender Configurations
User goal: Find, continue, or create an IT tender configuration.
Single user decision: Which IT tender configuration should I open or create?

Use procurement-facing language only.

Page title:
IT Tender Configurations

Subtitle:
Create or continue IT tender configurations from approved procurement packages.

Primary button:
Create IT Tender Configuration

Table columns:
- Tender Ref
- Tender Title
- Planning Package Ref
- Procuring Entity
- Procurement Method
- Status
- Issues
- Last Updated
- Action

Allowed dashboard status labels:
- In configuration
- Needs attention
- Ready for validation
- Under review
- Approved for preview
- Publication ready

Row action labels:
- Continue
- Fix
- Review
- Open

Create modal:
Title: Create IT Tender Configuration
Helper text: Select the approved procurement package that requires an IT tender configuration. The planning reference, procuring entity, procurement method, and applicable standard tender document will be filled from the package.

Modal fields:
- Approved Procurement Package
- Planning Package Ref
- Procuring Entity
- Procurement Method
- Standard Tender Document

Modal buttons:
- Cancel
- Create Configuration

Do not show:
Tender Shell, Tender to Configure, TenderSTDInstance, STD binding, STD package code, schema version, hash, rule ID, source anchor, render block, clause tree, or publication controls.
```

---

## 12. Cursor Prompt

```text
Refactor Screen 01 as the IT Tender Configurations dashboard.

Primary goal:
Help the user find, continue, or create an IT tender configuration.

Lifecycle rule:
Creation starts from an Approved Procurement Package, not a Tender Shell and not a Tender to Configure.

Required API shape:
{
  configurations: [
    {
      configuration_id,
      tender_ref,
      tender_title,
      planning_package_ref,
      procuring_entity_name,
      procurement_method_label,
      wizard_status_label,
      blocker_count,
      warning_count,
      last_updated_at,
      last_updated_by,
      action_label,
      route
    }
  ],
  create_options: [
    {
      procurement_package_id,
      procurement_package_label,
      planning_package_ref,
      procuring_entity_name,
      procurement_method_label,
      standard_tender_document_label,
      standard_tender_document_selectable
    }
  ]
}

Behavior:
1. Render page title "IT Tender Configurations".
2. Render subtitle "Create or continue IT tender configurations from approved procurement packages."
3. Render primary button "Create IT Tender Configuration".
4. Table columns must be Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Status, Issues, Last Updated, Action.
5. The create modal must select Approved Procurement Package.
6. After package selection, fill Planning Package Ref, Procuring Entity, Procurement Method, and Standard Tender Document.
7. Primary modal button must be "Create Configuration".
8. Do not render internal terms or IDs except configuration_id internally for routing.

Forbidden default UI terms:
Tender Shell, Tender to Configure, TenderSTDInstance, STD binding, STD package code, schema version, hash, rule ID, source anchor, render block, clause tree.
```

---

## 13. Acceptance Checklist

| Test | Pass condition |
|---|---|
| Lifecycle correctness | Creation starts from Approved Procurement Package |
| User language | No internal system terms appear |
| Decision clarity | User can identify what to open or create |
| Simplicity | No configuration data appears in the dashboard |
| Modal clarity | Only one active choice: Approved Procurement Package |
| Routing | Every row action opens the correct configuration or step |
