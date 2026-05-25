# KenTender Strategy Visual Hierarchy Differentiation Recommendations

This document reviews the highlighted controls on the Strategy Management screen and recommends how to visually differentiate queues, primary actions, record actions, primary tabs, secondary tabs, and inline row actions.

The current screen is structurally much better than earlier iterations, but the visual language is too flat. Many different UI elements use the same pill shape, same black selected state, same light-gray background, and similar spacing. As a result, the user has to read every control instead of understanding the screen by hierarchy.

The core issue:

```text
Queue filters, tabs, sub-tabs, action buttons, and row actions all look like the same component.
```

They are not the same concept. They need distinct visual treatments.

---

# 1. Controls That Currently Look Too Similar

The highlighted areas include:

1. **Global status queues**
   - `All`, `Draft`, `Submitted`, `Approved`, `Active`, `Archived`

2. **Primary create action**
   - `New Strategic Plan`

3. **Primary record tabs**
   - `Plan Info`, `Structure`, `Review`, `Audit`

4. **Secondary structure tabs**
   - `Overview`, `Programs`, `Sub-programs`, `Indicators`, `Targets`

5. **Contextual add action**
   - `Add Target`

6. **Inline row action**
   - `Edit`

Currently, these all share too much of the same visual vocabulary.

---

# 2. Recommended Visual Hierarchy

Use a strict component hierarchy:

```text
Global queue filters     = compact filter chips
Primary page action      = solid button
Primary record tabs      = underline tabs or segmented tabs
Secondary tabs           = smaller text tabs or subtle pills
Contextual add action    = secondary button with icon or outline
Inline row action        = low-emphasis text/link button
```

Each control type should have a different visual role.

---

# 3. Global Queue Filters

## Current Problem

The queue filters use the same selected black pill style as tabs and actions.

```text
[All 12] [Draft 10] [Submitted 0] [Approved 0] [Active 2] [Archived 0]
```

The selected `All` chip looks similar to selected tabs and primary buttons.

## Recommendation

Make queue filters look like compact status filters, not buttons.

Recommended visual style:

```text
All 12   Draft 10   Submitted 0   Approved 0   Active 2   Archived 0
```

Use:

- small height: 28–32px
- light background for inactive filters
- selected state with left accent bar or subtle filled background
- avoid pure black if black is also used for primary actions
- muted color for zero-count filters

## Suggested Queue Style

```css
.status-filter-row {
  display: flex;
  gap: 6px;
  align-items: center;
}

.status-filter {
  height: 30px;
  padding: 0 10px;
  border-radius: 8px;
  background: #f5f5f5;
  color: #444;
  font-weight: 500;
}

.status-filter.is-active {
  background: #eef4ff;
  color: #123a7a;
  box-shadow: inset 3px 0 0 #2563eb;
}

.status-filter.is-zero {
  color: #999;
}
```

## Design Rule

Queues are filters, not workflow actions. They should not look like command buttons.

---

# 4. Primary Page Action: New Strategic Plan

## Current Problem

`New Strategic Plan` uses the same solid black style that is also used for selected tabs and other add buttons.

This weakens the meaning of black.

## Recommendation

Reserve the strongest solid button style for page-level primary action only.

`New Strategic Plan` should remain visually strong because it creates a new top-level record.

Recommended style:

```text
[+ New Strategic Plan]
```

Use:

- solid dark button
- plus icon
- larger height than filters/tabs
- right-aligned in page header
- do not reuse this style for selected tabs

## Suggested Style

```css
.primary-page-action {
  height: 38px;
  padding: 0 16px;
  border-radius: 10px;
  background: #111;
  color: white;
  font-weight: 700;
}
```

## Design Rule

Only one visually dominant primary action should exist in the page header.

---

# 5. Primary Record Tabs

## Current Problem

The primary tabs currently look like pill buttons:

```text
[Plan Info] [Structure] [Review] [Audit]
```

Selected `Structure` is black, making it compete with the `New Strategic Plan` and `Add Target` buttons.

## Recommendation

Use underline tabs for primary record tabs.

Recommended style:

```text
Plan Info    Structure    Review    Audit
             ━━━━━━━━━
```

Use:

- transparent background
- no pill container
- selected tab indicated by underline and stronger text
- no black fill

## Suggested Style

```css
.primary-tabs {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.primary-tab {
  padding: 10px 0;
  color: #666;
  font-weight: 500;
  background: transparent;
}

.primary-tab.is-active {
  color: #111;
  font-weight: 700;
  border-bottom: 2px solid #111;
}
```

## Design Rule

Primary tabs are navigation within the selected record. They should not look like actions.

---

# 6. Secondary Structure Tabs

## Current Problem

The secondary tabs look nearly identical to the primary tabs:

```text
[Overview] [Programs] [Sub-programs] [Indicators] [Targets]
```

Selected `Targets` is also black, making it visually compete with the primary tab and action buttons.

## Recommendation

Make secondary tabs smaller and lighter than primary tabs.

Recommended style:

```text
Overview · Programs · Sub-programs · Indicators · Targets
```

or subtle segmented pills:

```text
Overview   Programs   Sub-programs   Indicators   Targets
```

Selected secondary tab should use:

- light filled background
- medium border
- dark text
- no black fill

## Suggested Style

```css
.secondary-tabs {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.secondary-tab {
  height: 28px;
  padding: 0 10px;
  border-radius: 7px;
  color: #666;
  background: transparent;
  font-size: 13px;
}

.secondary-tab.is-active {
  background: #f0f2f5;
  color: #111;
  font-weight: 700;
  box-shadow: inset 0 -2px 0 #111;
}
```

## Design Rule

Secondary tabs must be visibly subordinate to primary tabs.

---

# 7. Contextual Add Action: Add Target

## Current Problem

`Add Target` uses the same solid black style as `New Strategic Plan`.

But `Add Target` is not a page-level primary action. It is a contextual action inside the Structure → Targets sub-section.

## Recommendation

Use a secondary button style for contextual add actions.

Recommended style:

```text
[+ Add Target]
```

Use:

- outline or light filled background
- plus icon
- smaller than page primary button
- placed near the section heading, not floating alone

Better placement:

```text
Targets                                      [+ Add Target]
```

not visually detached on the far right of a large panel.

## Suggested Style

```css
.context-action {
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid #d0d5dd;
  background: #fff;
  color: #111;
  font-weight: 600;
}

.context-action:hover {
  background: #f9fafb;
}
```

## Design Rule

Only top-level creation uses solid black. Section-level creation uses outline or subtle fill.

---

# 8. Inline Row Action: Edit

## Current Problem

The row-level `Edit` action appears as a small gray pill button.

This is acceptable, but it still participates in the same pill-button visual language.

## Recommendation

Use a low-emphasis text action or icon button for row actions.

Recommended:

```text
Edit
```

or:

```text
✎
```

Use:

- text link style
- small icon button
- no heavy filled pill
- only visible on hover if the table becomes dense

## Suggested Style

```css
.row-action {
  color: #2563eb;
  font-weight: 500;
  background: transparent;
  border: none;
  padding: 4px 6px;
}
```

## Design Rule

Row actions should be the quietest actionable controls on the page.

---

# 9. Recommended Button and Navigation Taxonomy

Use this taxonomy across KenTender modules:

| UI Element | Purpose | Visual Treatment |
|---|---|---|
| Page primary action | Create top-level record | Solid dark button |
| Context action | Add child item / section action | Outline or light button |
| Workflow primary action | Submit / Approve / Publish | Solid colored or solid dark depending state |
| Destructive action | Cancel / Reject / Delete | Red outline or danger button |
| Queue filter | Filter list by state | Compact chip, not button-like |
| Primary tab | Navigate selected record sections | Underline tab |
| Secondary tab | Navigate subsection | Small subtle tab/pill |
| Row action | Edit one table row | Text link or small icon |

This prevents every clickable thing from becoming a pill.

---

# 10. Recommended Visual Rewrite of the Highlighted Areas

## Current

```text
[All 12] [Draft 10] [Submitted 0] [Approved 0] [Active 2] [Archived 0]

[New Strategic Plan]

[Plan Info] [Structure] [Review] [Audit]

[Overview] [Programs] [Sub-programs] [Indicators] [Targets]

[Add Target]
```

## Recommended

```text
Status filters
All 12   Draft 10   Submitted 0   Approved 0   Active 2   Archived 0
```

Top-right:

```text
[+ New Strategic Plan]
```

Primary tabs:

```text
Plan Info    Structure    Review    Audit
             ━━━━━━━━━
```

Secondary tabs:

```text
Overview   Programs   Sub-programs   Indicators   Targets
                                               ━━━━━━━
```

Section header:

```text
Targets                                           [+ Add Target]
```

Table row:

```text
Edit
```

---

# 11. Stronger Layout Arrangement

Inside the selected plan panel, use this hierarchy:

```text
Test Strategic Plan 2026–2030
MOH · 2026–2030 · Version 1
[Draft] [Ready for downstream use]

Programs 2   Sub-programs 1   Indicators 1   Targets 1

Plan Info    Structure    Review    Audit
             ━━━━━━━━━

Structure
Overview   Programs   Sub-programs   Indicators   Targets
                                               ━━━━━━━

Targets                                      [+ Add Target]

Name              Indicator        Period        Actions
Test target       Test indicator   2026          Edit
```

This makes each layer distinct:

- title area: identity
- metrics: summary
- primary tabs: selected record navigation
- secondary tabs: structure subsection
- add target: section action
- edit: row action

---

# 12. Spacing Rules

Use spacing to reinforce hierarchy.

Recommended vertical spacing:

```text
Page title to status filters: 16px
Status filters to workbench: 12px
Selected record header to metrics: 16px
Metrics to primary tabs: 14px
Primary tabs to secondary tabs: 14px
Secondary tabs to section heading: 12px
Section heading to table: 10px
```

Do not use the same vertical spacing between every element. Equal spacing makes the hierarchy harder to read.

---

# 13. Shape Rules

Do not use the same pill shape for everything.

Recommended shapes:

```text
Queue filters: compact rounded rectangle, radius 8px
Primary page button: rounded rectangle, radius 10px
Primary tabs: no pill, underline only
Secondary tabs: very subtle rounded rectangle, radius 6px
Status badges: pill, radius 999px
Context actions: outline rounded rectangle, radius 8px
Row actions: text link or icon only
```

This gives each element a distinct identity.

---

# 14. Color Rules

Current black is overused.

Recommended color hierarchy:

```text
Black solid: page-level primary action only, or one critical workflow action
Dark underline: active primary tab
Light blue / neutral accent: active queue filter
Light gray: inactive chips or secondary tabs
Green: active/ready/approved status badges
Amber: draft/warning status badges
Red: destructive or blocked states only
Blue text: links and informational actions
```

Do not use black fill for:

- selected queue
- selected primary tab
- selected secondary tab
- section add action
- row edit action

all at the same time.

---

# 15. Count Display Rules

Counts should not all have the same visual weight.

Recommended:

```text
All 12
Draft 10
Submitted 0
Approved 0
Active 2
Archived 0
```

Use:

- normal weight for nonzero counts
- muted text for zero counts
- optionally small count badge for nonzero values

Example:

```text
Draft 10
Submitted 0  // muted
Approved 0   // muted
Active 2
```

This helps the user notice meaningful queues quickly.

---

# 16. Recommended Component Tokens

Use reusable component classes across KenTender:

```text
kt-page-action-primary
kt-context-action
kt-status-filter
kt-status-filter-active
kt-primary-tab
kt-primary-tab-active
kt-secondary-tab
kt-secondary-tab-active
kt-row-action
kt-status-badge
kt-destructive-action
```

This will prevent future screens from drifting back into one generic pill style.

---

# 17. Immediate Changes to Make

In order:

1. **Stop using black filled pills for selected tabs.**
   - Use underline tabs for primary tabs.

2. **Reserve solid black for `New Strategic Plan` only.**
   - Or for one primary workflow action if no page create action exists.

3. **Change queue selected state from black fill to accent filter style.**
   - Example: light blue fill with left accent bar.

4. **Make secondary tabs visually smaller than primary tabs.**
   - No black fill.

5. **Change `Add Target` to an outline/context button.**
   - Add plus icon.

6. **Change row `Edit` to a text link or icon action.**

7. **Add a section heading above the second-level tabs and table.**
   - Example: `Structure` then `Targets`.

8. **Apply muted style to zero-count queues.**

9. **Create reusable KenTender component classes.**
   - Do not hand-style each screen independently.

---

# 18. Final Recommendation

The Strategy screen is structurally good now. The next improvement is visual grammar.

Every clickable control should answer this question visually:

```text
Am I filtering a list?
Am I navigating within a record?
Am I creating something?
Am I editing one row?
Am I triggering workflow?
```

Right now, too many controls answer with the same visual style.

Adopt this rule:

```text
Queues filter.
Tabs navigate.
Buttons act.
Badges inform.
Links edit small things.
```

Once this distinction is enforced, the screen will feel much more professional, calmer, and easier to use without changing the underlying functionality.

