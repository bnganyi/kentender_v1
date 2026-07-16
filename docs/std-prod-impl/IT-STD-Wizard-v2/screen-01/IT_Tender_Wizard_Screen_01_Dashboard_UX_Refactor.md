# IT Tender Wizard Screen 01 — Configuration Dashboard UX Refactor

**Project:** KenTender e-Procurement System  
**Module:** IT Tender Configuration Wizard  
**Screen:** 01 — Configuration Dashboard  
**Status:** UX refactor specification  
**Design mode:** Simplification-first  

---

## 1. User Journey

A procurement user opens the IT Tender Wizard to find, resume, review, or create an IT tender configuration.

The user should immediately understand:

1. Which IT tender configurations exist.
2. Which ones need action.
3. Which one they should open next.
4. Whether they can create a new configuration.

This screen is a **work queue**, not a configuration form.

---

## 2. Single User Decision

> Which IT tender configuration do I open or create?

Everything on the screen must support that decision.

---

## 3. IT STD Grounding

This screen is not directly mapped to one IT STD section. It is a workflow entry screen for configuring a tender against the approved IT STD structure.

The screen exists because the IT STD requires a controlled tender document composed of the standard tendering sections, including:

- Tender Data Sheet;
- Evaluation and Qualification Criteria;
- Tendering Forms;
- Requirements of the Information System;
- Technical Requirements;
- Implementation Schedule;
- System Inventory Tables;
- Background and Informational Materials;
- Contract sections.

The dashboard must therefore help the user enter or resume a controlled configuration. It must not expose the legal or technical complexity of those sections on the landing page.

The IT STD also distinguishes locked standard text from tender-specific customization. ITT and GCC text are not edited directly; tender-specific values are supplied through controlled surfaces such as TDS and SCC. The dashboard should respect that boundary.

---

## 4. Screen Ownership

| Item | Decision |
|---|---|
| Screen owns | Configuration list, filtering, creation entry point, resume/open action |
| Primary object | `TenderSTDConfigurationSummary` |
| Editable here | Filters, search, sorting, view preference only |
| Actions here | Create configuration, open configuration, continue setup, view blockers |
| Read-only references | Tender Ref, Tender Title, Planning Package Ref, Procuring Entity, Procurement Method, Wizard State, validation summary, last updated, next action |
| Must not own | TDS values, requirements, schedule, inventory, price schedule, evaluation, forms, SCC, approval decisions, publication |

---

## 5. Default Layout

### Header

Title:

```text
IT Tender Configurations
```

Subtitle:

```text
Create, resume, and review IT tender configurations prepared under the active IT Standard Tender Document.
```

Primary action:

```text
Create Tender Configuration
```

Do not use:

```text
Create Tender
Create STD
Generate Tender
Publish Tender
```

---

### Summary Cards

Use a maximum of four cards:

| Card | Meaning |
|---|---|
| In Configuration | Draft configurations still being completed |
| Needs Action | Configurations with blockers or returned corrections |
| Ready for Review | Configurations that passed validation and can be reviewed |
| Publication Ready | Configurations handed off or ready for Tender Management |

Do not show technical counts such as rule IDs, section hashes, source anchors, or render block totals.

---

### Main Table

Recommended columns:

| Column | Display rule |
|---|---|
| Tender | Show Tender Ref and Tender Title. Planning Package Ref may appear as small subtext. |
| Procuring Entity | Plain name. |
| Procurement Method | Plain label, for example `Open National Tender`. |
| Wizard State | Human-readable state. |
| Progress | Simple completion indicator. |
| Issues | `0 Blockers / 2 Warnings`, not detailed findings. |
| Next Action | One clear action: Continue Setup, Fix Blockers, Submit for Review, Open Preview, Open in Tender Management. |
| Updated | Last updated date/time. |

Keep the table focused. Do not add section-by-section technical status columns.

---

## 6. State Labels

Use user-facing labels, not internal enums.

| Internal state | User-facing label |
|---|---|
| `IN_CONFIGURATION` | In configuration |
| `VALIDATION_FAILED` | Needs action |
| `READY_FOR_REVIEW` | Ready for review |
| `UNDER_REVIEW` | Under review |
| `RETURNED_FOR_CORRECTION` | Returned for correction |
| `APPROVED_FOR_RENDER` | Approved for preview |
| `PREVIEW_CONFIRMED` | Preview confirmed |
| `PUBLICATION_READY` | Publication ready |

The internal state may remain available in API data, but the default UI should use readable labels.

---

## 7. Create Configuration Flow

Clicking **Create Tender Configuration** opens a short modal or side panel.

Required fields:

| Field | Rule |
|---|---|
| Tender Shell / Tender Ref | Required. Must already exist or be selected from eligible tender shells. |
| Planning Package Ref | Read-only once tender shell is selected. |
| Procuring Entity | Read-only from tender shell. |
| Procurement Method | Read-only or controlled from tender shell/TDS setup rules. |
| STD Package | Default to active IT STD version. Advanced users may view details, not change legal text. |

Primary action:

```text
Start Configuration
```

Cancel action:

```text
Cancel
```

Creation must not ask the user to configure requirements, TDS, price schedules, evaluation, or SCC in this modal.

---

## 8. Validation Behavior

Dashboard validation must be calm.

Allowed:

```text
0 Blockers / 2 Warnings
3 Blockers
Ready for review
```

Not allowed:

```text
RULE_TDS_004 failed
Section VII unresolved
Hash mismatch
Render block missing
```

Detailed findings belong in the Validation Report screen.

---

## 9. Forbidden Complexity

Do not show on this screen:

- clause text;
- STD section trees;
- source-document hashes;
- render-block diagnostics;
- detailed validation findings;
- editable TDS values;
- requirement rows;
- price schedule lines;
- evaluation scores;
- SCC terms;
- approval decision controls;
- publish buttons.

The dashboard is navigation and triage only.

---

## 10. Stitch Prompt

```text
Design Screen 01 for the KenTender IT Tender Configuration Wizard.

Screen name: IT Tender Configurations
User goal: Find, resume, review, or create an IT tender configuration.
Single user decision: Which IT tender configuration do I open or create?

Keep the screen simple. This is a work queue, not a configuration form.

Use this layout:
1. Page header with title "IT Tender Configurations".
2. Short subtitle: "Create, resume, and review IT tender configurations prepared under the active IT Standard Tender Document."
3. Primary button: "Create Tender Configuration".
4. Four summary cards only: In Configuration, Needs Action, Ready for Review, Publication Ready.
5. Search and filter bar.
6. Main table with columns:
   - Tender
   - Procuring Entity
   - Procurement Method
   - Wizard State
   - Progress
   - Issues
   - Next Action
   - Updated

Tender cell should show Tender Ref and Tender Title, with Planning Package Ref as small subtext.

Use human-readable labels:
- In configuration
- Needs action
- Ready for review
- Under review
- Returned for correction
- Approved for preview
- Preview confirmed
- Publication ready

Allowed row actions:
- Continue Setup
- Fix Blockers
- Submit for Review
- Open Preview
- Open in Tender Management

Do not show STD hashes, clause trees, render diagnostics, technical source anchors, TDS fields, requirements, price schedule lines, evaluation scoring, SCC terms, approval controls, or publish buttons.

Create Tender Configuration should open a simple modal with:
- Tender Shell / Tender Ref
- Planning Package Ref
- Procuring Entity
- Procurement Method
- STD Package
- Start Configuration button

The modal must not ask the user to configure TDS, requirements, pricing, evaluation, SCC, or publication.
```

---

## 11. Cursor Prompt

```text
Refactor Screen 01 of the IT Tender Configuration Wizard as a focused configuration dashboard.

Purpose:
The dashboard is a work queue for IT tender configurations. It must help users choose which configuration to open or create. It must not become a configuration or legal metadata screen.

Primary object:
TenderSTDConfigurationSummary

Required API shape:
{
  configuration_id,
  tender_ref,
  tender_title,
  planning_package_ref,
  procuring_entity_name,
  procurement_method_label,
  wizard_state,
  wizard_state_label,
  progress_percent,
  blocker_count,
  warning_count,
  next_action,
  next_action_label,
  last_updated_at,
  owner_name
}

Screen behavior:
1. Render title: IT Tender Configurations.
2. Render primary button: Create Tender Configuration.
3. Render four summary cards:
   - In Configuration
   - Needs Action
   - Ready for Review
   - Publication Ready
4. Render search and filters.
5. Render table columns:
   - Tender
   - Procuring Entity
   - Procurement Method
   - Wizard State
   - Progress
   - Issues
   - Next Action
   - Updated
6. Tender cell shows tender_ref, tender_title, and planning_package_ref as subtext.
7. Issues cell shows simple counts only, e.g. "0 Blockers / 2 Warnings".
8. Next Action must be one of:
   - Continue Setup
   - Fix Blockers
   - Submit for Review
   - Open Preview
   - Open in Tender Management

Create flow:
Opening Create Tender Configuration must show a minimal modal or drawer:
- select eligible Tender Shell / Tender Ref;
- show Planning Package Ref read-only after selection;
- show Procuring Entity read-only;
- show Procurement Method read-only or controlled;
- show active STD Package read-only with View Details link;
- action: Start Configuration.

Rules:
- Do not hardcode realistic tender data outside seeded fixtures.
- Do not display STD hashes, source anchors, clause trees, render block diagnostics, or audit metadata in the default view.
- Do not display editable TDS, requirements, implementation schedule, inventory, pricing, evaluation, forms, or SCC fields on this screen.
- Do not show approval or publication controls.
- Use user-facing state labels, not raw enum names.
- Validation details must link to Validation Report; this screen only shows blocker/warning counts.

Acceptance criteria:
- A procurement user can identify which configuration to open in under 10 seconds.
- All visible tender values come from the API or explicit seed fixtures.
- Create flow requires an eligible tender shell and active IT STD package.
- No detailed configuration fields appear on the dashboard.
- No magical or unexplained values appear.
```

---

## 12. Acceptance Checklist

| Test | Pass condition |
|---|---|
| User decision clarity | User can tell whether to create, continue, fix, review, preview, or hand off. |
| STD grounding | Screen routes users into the controlled IT STD configuration; it does not edit locked STD content. |
| Simplicity | No detailed legal, technical, pricing, evaluation, or contract configuration appears. |
| No magical values | Every displayed value comes from the configuration summary API or seeded fixture data. |
| State clarity | Internal states are converted to readable labels. |
| Validation calmness | Only blocker/warning counts appear. Detailed findings are linked out. |
| Creation gate | New configuration requires eligible tender shell and active IT STD package. |

---

## 13. Final Rule

If the field does not help the user decide which configuration to open or create, remove it from Screen 01.
