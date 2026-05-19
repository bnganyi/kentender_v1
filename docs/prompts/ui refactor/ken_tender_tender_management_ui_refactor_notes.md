# KenTender Tender Management UI Refactor Notes

KenTender is an end-to-end comprehensive eProcurement system being developed on the Frappe ERPNext framework. The attached screenshots show the Tender Management module. The current Tender Management UI is cognitively heavy, overloaded with text, visually unbalanced, forces users to scroll up and down, and uses screen space poorly. The top section for menus and controls consumes almost half of the screen before real tender data is shown.

The core issue is not only visual density. The screen has **no clear hierarchy**. The user sees module labels, queue labels, KPI labels, scope filters, search, filter panel, tender list, tender detail, action buttons, detail tabs, status cards, readiness checks, timelines, audit references, and technical IDs all competing at the same level.

For a government procurement system, the UI must remain audit-rich, but the audit depth should be **progressively disclosed**, not dumped into the primary work surface.

---

## 1. Primary Diagnosis

### Current Issues

The page currently has these structural problems:

1. **The top utility/menu area consumes too much vertical space**
   - Page title
   - Subtitle
   - Long implementation note text
   - KPI strip
   - Scope filters
   - Queue filters
   - Search/filter controls

   By the time the user reaches real tender data, nearly half the screen is gone.

2. **Queues, statuses, KPIs, and filters are duplicated**
   - “Draft”, “Published”, “Addenda”, “Opening Ready” appear in multiple places.
   - The KPI strip and queue strip overlap conceptually.
   - This creates decision fatigue.

3. **The tender detail panel is overloaded**
   - It mixes operational status, STD binding, readiness, outputs, timeline, supplier access, blockers, actions, next steps, readiness criteria, tender summary, key dates, recent events, and technical references.

4. **Important information is visually weak**
   - The actual lifecycle state should dominate the screen.
   - Instead, it appears inside small gray cards with the same weight as secondary metadata.

5. **The UI exposes internal codes too early**
   - Codes like `STD-OUT-04316`, `PUBSNAP-TND...`, `TRD...`, `DSM`, `DOM`, `DEM`, `DCM` are useful for audit and debugging, but they should not sit in the main operational view unless the user opens “Technical / Audit references”.

6. **Scrolling breaks context**
   - The user scrolls down to readiness or events and loses the tender list, actions, selected tender context, and tabs.
   - That is dangerous in workflow-heavy government systems.

---

# Recommended Refactor: Three-Zone Workbench

Use a **three-zone layout**:

```text
┌──────────────────────────────────────────────────────────────┐
│ Compact module header + primary actions                      │
├───────────────┬──────────────────────────────────────────────┤
│ Tender list   │ Selected tender work area                    │
│ + filters     │                                              │
│               │  Summary ribbon                              │
│               │  Lifecycle actions                           │
│               │  Focused tab content                         │
└───────────────┴──────────────────────────────────────────────┘
```

The goal is simple:

- Left side: choose the tender.
- Top of detail area: understand status and next action.
- Main area: work on one focused task.
- Audit/technical detail: available, but not dominant.

---

## 2. Refactor the Top of the Page

### Current Top Section Should Be Reduced by About 70%

Remove this long implementation descriptor from the visible UI:

> Workbench shell (P9-01–P9-02). New Tender wizard...

That text is developer/spec metadata. It should never appear in production user UI. Move it to internal documentation, feature flags, or admin debug mode.

### Proposed Compact Header

```text
Tender Management                                  [Evidence Export] [New Tender]

Manage tender creation, publication, amendments, closing, and handoff.
```

That is enough.

Then immediately show the workbench.

---

## 3. Replace KPI Strip + Queues with a Single Lifecycle Command Bar

Right now the UI has:

- KPI strip
- Scope chips
- Queue chips
- Search
- Filters

This is too many horizontal navigation layers.

Use one compact lifecycle bar:

```text
All  Draft  Review  Approved  Published  Clarifications  Addenda  Closing Soon  Opening Ready  Closed
```

Each item can show a count:

```text
All 12 | Draft 3 | Review 0 | Approved 2 | Published 3 | Clarifications 5 | Addenda 0
```

Do not repeat “KPI strip” and “Queues”. One row is enough.

### Better Version

Use grouped lifecycle stages:

```text
Preparation        Review & Publication        Live Tender        Closing & Handoff
Draft 3            Review 0  Approved 2        Published 3        Closing Soon 0
STD Incomplete 0                              Clarifications 5    Opening Ready 0
                                              Addenda 0           Closed 0
```

This gives users a mental model of the tender lifecycle instead of a flat chip soup.

---

## 4. Make Search and Filters Left-Panel Concerns

Search and filters should belong to the tender list, not the whole page.

### Proposed Left Panel

```text
Tender list
[ Search tender, package, supplier... ]

Status: Published
Entity: All
Procurement method: All
Readiness: Any

────────────────────────
TND-MOH-2029-0007
B3 Package 24c6
Published · STD Ready
Submission: 01 Jun 2026
No blockers

TND-MOH-2029-0005
B3 Package 2448
Published · STD Ready
Submission: 01 Jun 2026
No blockers
```

Keep tender cards tight. Each card should show only:

- Tender code
- Package/title
- State
- Readiness
- Next deadline
- Blocker state

Everything else belongs in the detail panel.

---

## 5. Redesign the Selected Tender Header

The selected tender detail needs a persistent, compact header that remains visible while scrolling.

### Proposed Selected Tender Header

```text
TND-MOH-2029-0007 · B3 Package 24c6
MOH · Open Tender · Goods

Published       STD Ready       Supplier Access Valid       No Blockers
Submission: 01 Jun 2026, 19:26   Opening: 02 Jun 2026, 19:26

Next step: Monitor lifecycle and downstream work
[View] [Create Addendum] [Clarifications] [Prepare Opening] [Cancel Tender ▾]
```

This replaces many of the current gray boxes.

### Why This Works

The user immediately sees:

- What tender am I looking at?
- What state is it in?
- Is it compliant?
- What is the next deadline?
- What can I do now?

That is the operational core.

---

## 6. Replace the Gray Card Grid with a Status Ribbon

The current cards are:

- Tender state
- STD binding
- Readiness
- Outputs
- Publication snapshot
- Timeline
- Supplier access
- Blockers

These are all equally weighted. They should not be.

Use a compact status ribbon:

```text
Lifecycle: Published
STD: April 2022 · Bound
Readiness: Ready
Supplier Access: Valid
Blockers: 0 open
Outputs: Complete
```

Each item can be clickable and open a drawer or tab.

For example:

```text
[Lifecycle Published] [STD Ready] [Access Valid] [Outputs Complete] [0 Blockers]
```

Use color carefully:

- Green: ready/valid/complete
- Amber: warning/incomplete
- Red: blocker/not assessed
- Gray: not applicable or unavailable

Do not use red text for every incomplete thing unless it blocks the next action.

---

## 7. Change Tabs from Many Equal Tabs to Task Groups

Current tabs:

```text
Overview | STD & Readiness | Timeline | Supplier Access | Clarifications | Addenda | Submissions | Opening Readiness | Evaluation Handoff | Contract Handoff | Audit & Evidence
```

This is too many for one horizontal tab row.

Group them into 4 or 5 task areas:

```text
Overview
Preparation
Live Tender
Handoff
Audit
```

Then use sub-sections inside each.

### Proposed Tab Structure

#### Overview

- Tender summary
- Current state
- Next action
- Key dates
- Blockers
- Recent activity

#### Preparation

- STD binding
- Document readiness
- Output bundle
- Supplier submission model
- Opening/evaluation rules

#### Live Tender

- Supplier access
- Clarifications
- Addenda
- Submissions

#### Handoff

- Opening readiness
- Evaluation handoff
- Contract handoff

#### Audit

- Timeline
- Evidence
- Denied actions
- Technical references

This keeps the UI legally defensible without making the primary screen unreadable.

---

## 8. Use a Right-Side Drawer for Technical References

Technical IDs should not appear in the main operational area.

Move these into a drawer:

```text
Technical References
────────────────────
STD Template: KE-PPRA-WORKS-BLDG-2022-04-POC
Version: April 2022
Publication Snapshot: PUBSNAP-TND-MOH-2029-0007-TM2

Outputs
Bundle: STD-OUT-04316
DSM: STD-OUT-04317
DOM: STD-OUT-04318
DEM: STD-OUT-04319
DCM: STD-OUT-04320
```

Access via:

```text
[Technical references]
```

or from the Audit tab.

This preserves auditability while protecting normal users from noise.

---

# Proposed Redesigned Page Layout

## Desktop Layout

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Tender Management                                      [Export] [New Tender]│
│ Manage tender creation, publication, amendment, closing, and handoff.       │
├─────────────────────────────────────────────────────────────────────────────┤
│ All 12 | Draft 3 | Review 0 | Approved 2 | Published 3 | Addenda 0 | Closed │
├───────────────────────┬─────────────────────────────────────────────────────┤
│ Tender list           │ TND-MOH-2029-0007 · B3 Package 24c6                 │
│ [Search...]           │ MOH · Open Tender · Goods                           │
│                       │                                                     │
│ Status: Published     │ [Published] [STD Ready] [Access Valid] [No Blockers]│
│ Readiness: Any        │ Submission: 01 Jun 2026 · Opening: 02 Jun 2026      │
│ Method: All           │                                                     │
│                       │ Next step: Monitor lifecycle and downstream work     │
│ ┌───────────────────┐ │ [View] [Clarifications] [Addendum] [Opening] [More] │
│ │ TND-MOH-2029-0007 │ ├─────────────────────────────────────────────────────┤
│ │ B3 Package 24c6   │ │ Overview | Preparation | Live Tender | Handoff |Audit│
│ │ Published         │ ├─────────────────────────────────────────────────────┤
│ │ STD Ready         │ │ Key dates                                           │
│ │ No blockers       │ │ Submission deadline        01 Jun 2026, 19:26       │
│ └───────────────────┘ │ Opening scheduled          02 Jun 2026, 19:26       │
│                       │                                                     │
│ ┌───────────────────┐ │ Blockers                                            │
│ │ TND-MOH-2029-0005 │ │ No tender-level blockers.                           │
│ └───────────────────┘ │                                                     │
│                       │ Recent activity                                     │
│                       │ Tender Published                                    │
└───────────────────────┴─────────────────────────────────────────────────────┘
```

This layout eliminates the massive vertical preamble and brings real data above the fold.

---

## 9. Redesign the Readiness View

The readiness view currently lists checks with repeated “Not met” text and long explanations. It should become a compact checklist with severity and remediation action.

### Current

```text
Tender document package ready        Not met
Regenerate tender document bundle after updating STD parameters.

Supplier submission checklist ready  Not met
Generate supplier submission model after completing tender parameters.
```

### Proposed

```text
Tender document readiness                 Not Assessed

Required before publication
────────────────────────────────────────────
✕ Document bundle              Regenerate bundle
✕ Supplier submission model     Generate model
✕ Opening register rules        Generate rules
✕ Evaluation rules              Complete document readiness first
✕ Contract carry-forward terms  Generate terms
```

Better yet, use actionable rows:

```text
Requirement                    Status       Action
Document bundle                Missing      Generate
Supplier submission model      Missing      Generate
Opening register rules         Missing      Generate
Evaluation rules               Blocked      Resolve readiness first
Contract carry-forward terms   Missing      Generate
```

This turns diagnosis into workflow.

---

## 10. Reduce Card Text Aggressively

Current tender cards are too text-heavy.

### Current Card

```text
TND-MOH-2029-0007 · B3 Package 24c6
Package: PKG-B3-2029-1968 · Open Tender · Goods
Entity: MOH
Status: Published · STD: April 2022 · Readiness: Ready
Deadline: 01-06-2026 19:26:02 Africa/Nairobi
No blockers
Published Goods STD Ready
```

### Better Card

```text
TND-MOH-2029-0007
B3 Package 24c6

Published · Open Tender · Goods
STD Ready · No blockers
Submission: 01 Jun 2026, 19:26
```

Remove labels where the meaning is obvious. For example, users do not need to see `Status:` before every status.

---

## 11. Separate Operational Users from Audit/Admin Users

A procurement officer and an audit/admin user should not have the same default view.

### Procurement Officer Default View

Show:

- State
- Next action
- Deadline
- Blockers
- Documents/readiness
- Clarifications/addenda/submissions

Hide by default:

- Output codes
- Publication snapshot IDs
- Technical references
- Full event log

### Auditor/Admin Default View

Show:

- Timeline
- Evidence
- Denied actions
- Approvals
- State transitions
- Snapshot references
- Document output references

This can be achieved through role-based default tabs, not separate modules.

---

# 12. Specific Changes to Make Immediately

## Change 1: Remove the Implementation Note from Production UI

Remove:

```text
Workbench shell (P9-01–P9-02). New Tender wizard...
```

Replace with nothing, or move it into a debug-only “Implementation metadata” drawer.

---

## Change 2: Merge KPI and Queue Controls

Replace both with one lifecycle bar:

```text
All 12 | Draft 3 | Review 0 | Approved 2 | Published 3 | Clarifications 5 | Addenda 0 | Closing Soon 0
```

---

## Change 3: Make Tender Detail Header Sticky

Selected tender identity, status badges, deadlines, and actions should remain visible while the user scrolls.

---

## Change 4: Make Detail Panel Tab Content Scroll Independently

The tender list should stay in place. The selected tender header should stay in place. Only the tab body should scroll.

This prevents the current “scroll up/down to remember context” problem.

---

## Change 5: Move Technical Data to Audit / Technical Drawer

Move these out of the main view:

- Publication snapshot ID
- STD output IDs
- DSM/DOM/DEM/DCM codes
- Binding reference codes
- Detailed technical references

---

## Change 6: Convert Readiness Checks into a Work Queue

Instead of static explanatory text, use:

```text
Requirement | Status | Blocking? | Action
```

That makes the screen task-oriented.

---

## Change 7: Introduce a “Current Next Step” Component at the Top

This is good in the current UI, but it appears too low and gets buried.

Move it immediately below the selected tender header:

```text
Next step
Monitor lifecycle and downstream work.

Recommended actions:
[Review submissions] [Prepare opening] [View audit trail]
```

For draft tenders:

```text
Next step
Complete STD readiness before publication review.

Required:
[Bind STD] [Run readiness] [Generate document bundle]
```

---

# 13. Better Information Hierarchy

Use this display priority:

## Level 1 — Always Visible

- Tender code and title
- Current lifecycle state
- Readiness state
- Next deadline
- Blocker count
- Primary action

## Level 2 — One Click / One Tab

- Key dates
- Supplier access
- Clarifications
- Addenda
- Submissions
- Readiness checklist

## Level 3 — Audit/Admin Detail

- Event log
- Evidence export
- Denied actions
- Snapshot references
- STD output codes
- Technical references

Right now the screen shows Level 1, 2, and 3 at the same time. That is the core reason it feels heavy.

---

# 14. Suggested Visual Design Rules

Use these as implementation rules for the Frappe UI refactor:

1. **Maximum two horizontal control rows below the page header**
   - Lifecycle bar
   - Search/filter row or left-panel filters

2. **No production screen should show implementation page codes**
   - Hide `P9-01`, `P9-08`, etc.

3. **No more than 5 primary tabs**
   - Use grouped tabs.

4. **No more than 6 visible status badges**
   - Lifecycle, STD, readiness, access, blockers, deadline.

5. **Use drawers for rare-detail content**
   - Technical references, output IDs, audit events, evidence details.

6. **Use sticky selected-tender header**
   - Never make the user scroll back to know which tender they are editing.

7. **Use independent scrolling regions**
   - Sidebar/tender list scroll separately from detail content.

8. **Collapse completed/healthy sections**
   - Show warnings and blockers first.

9. **Make red mean blocking**
   - Do not use red for every incomplete background condition.

10. **Put actions near the state they affect**
   - Readiness actions inside readiness tab.
   - Addendum actions inside live tender tab.
   - Publication actions near lifecycle state.

---

# 15. Recommended Target Structure for Tender Management

```text
Tender Management
├── Lifecycle Queue Bar
├── Tender Workbench
│   ├── Left: Tender List + Filters
│   └── Right: Selected Tender
│       ├── Sticky Tender Header
│       ├── Status Ribbon
│       ├── Next Step
│       ├── Actions
│       └── Tabs
│           ├── Overview
│           ├── Preparation
│           ├── Live Tender
│           ├── Handoff
│           └── Audit
```

This gives a cleaner, defensible structure without weakening the governance requirements.

---

## Final Recommendation

Do **not** try to “beautify” the current screen. Refactor the information architecture.

The current UI is built like a diagnostic console. KenTender needs a **case-management workbench**: one selected tender, one current state, one next action, supporting evidence available when needed.

For this module, implement the refactor in this order:

1. Remove implementation metadata from the page.
2. Merge KPI and queue controls.
3. Create sticky selected-tender header.
4. Redesign tender cards.
5. Group tabs into five task areas.
6. Move technical/audit references into drawer or Audit tab.
7. Convert readiness into an actionable checklist.
8. Add role-based default views for procurement officer vs auditor/admin.

That will cut perceived complexity by more than half without removing any legally necessary information.

