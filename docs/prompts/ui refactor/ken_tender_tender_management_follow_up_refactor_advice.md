# KenTender Tender Management Follow-Up Refactor Advice

This document captures the follow-up UI review for the updated Tender Management screen after the first round of refactoring. It is intended to guide the next implementation pass separately from the first refactor notes.

The new version is materially better than the earlier version. The page now has a clearer workbench structure, the lifecycle queues are more understandable, and the selected tender context is stronger.

However, three major UI problems remain:

1. the **left tender list needs its own scrollbar**
2. the **queue command area is better, but still too tall**
3. the **detail action buttons are not placed correctly yet**

---

# 1. Left Tender List: Yes, It Should Have Its Own Scrollbar

The left tender list should absolutely scroll independently from the selected tender detail.

Right now, when the list grows, it pushes or fights with the detail content. That is not ideal for a workbench. The left panel should behave like an inbox or case list.

## Recommended Behavior

The overall page should have fixed-height workbench regions:

```text
Tender Management header
Lifecycle queue bar
────────────────────────
Left tender list      Selected tender detail
scrolls independently detail body scrolls independently
```

The left list should use an internal scroll container:

```css
height: calc(100vh - headerHeight - queueBarHeight);
overflow-y: auto;
```

The selected tender detail should also have an internal scroll region, but the tender identity/header/action area should remain sticky.

## Better Left Panel Structure

```text
Tender list
[Search...]

[My Work] [All]

All tenders

┌──────────────────────┐
│ TND-MOH-2029-0008    │
│ B3 Package 3fea      │
│ STD Incomplete       │
│ Not Ready · Blockers │
└──────────────────────┘

┌──────────────────────┐
│ TND-MOH-2029-0007    │
│ B3 Package 24c6      │
│ Published · Ready    │
│ Submission: 01 Jun   │
└──────────────────────┘
```

The list itself should scroll. The detail side should not move just because the user is browsing tenders.

## Also Reduce Card Height

The left tender cards are still too tall. They can be tightened.

### Current Card

```text
TND-MOH-2029-0007
B3 Package 24c6
Published · Open Tender · Goods
Ready · No blockers
Submission: 01-06-2026 19:26:02 Africa/Nairobi
No blockers
```

### Better Card

```text
TND-MOH-2029-0007
B3 Package 24c6
Published · Ready
Due 01 Jun 2026 · No blockers
```

Do not repeat “No blockers” twice.

---

# 2. Queue Commands: Better, But Still Too Large

The new grouped queue command area is a real improvement. It is much more understandable than the earlier KPI strip plus queue strip duplication.

The grouping is good:

```text
Preparation
Review & Publication
Live Tender
Closing & Handoff
```

That gives the user a lifecycle mental model.

However, it still consumes too much vertical space. It should be more compact.

## Current Problem

The queue bar is now visually cleaner, but it still occupies a large block near the top. The screen still delays real tender data.

## Recommended Queue Bar Design

Use a compact segmented lifecycle bar:

```text
All 9   Draft 3   STD Incomplete 1   Review 0   Approved 2   Published 3   Clarifications 5   Addenda 0   Closing Soon 0
```

Then optionally expose lifecycle grouping only when the user expands it.

## Better Compromise

Keep the grouping, but reduce vertical height:

```text
All 9
Preparation: Draft 3 · STD Incomplete 1
Review: Review 0 · Returned 0 · Approved 2
Live: Published 3 · Clarifications 5 · Addenda 0
Closing: Closing Soon 0 · Opening Ready 0 · Closed 0
```

This can fit in one or two lines instead of a large panel.

## Recommended Layout

Use this layout:

```text
[All 9]  Preparation: [Draft 3] [STD Incomplete 1]  Review: [Review 0] [Approved 2]  Live: [Published 3] [Clarifications 5] [Addenda 0]  Closing: [Opening Ready 0] [Closed 0]
```

If the user has a smaller screen, wrap it horizontally or make it horizontally scrollable.

The current version is better conceptually, but still oversized.

---

# 3. Detail Pane Actions: Not Placed Right Yet

The action buttons are currently sitting under “Current Next Step” as a long disabled button cloud:

```text
View
Edit draft
Bind STD
Run readiness
Submit for review
Return for correction
Approve publication
Publish
Cancel tender
Mark retender required
Supersede
```

This is not ideal.

It creates two problems:

1. The user sees too many actions at once.
2. Disabled actions create visual noise and make the page feel broken or unavailable.

For a workflow-heavy procurement system, actions should be state-aware and prioritized.

---

## Recommended Action Hierarchy

### Primary Action

Show one main recommended action.

For example, for a published tender:

```text
Primary action: Monitor tender
```

or:

```text
[View tender]
```

For a draft tender:

```text
[Complete STD readiness]
```

For a tender ready for review:

```text
[Submit for publication review]
```

For an approved tender:

```text
[Publish tender]
```

### Secondary Actions

Show 2–4 contextually relevant secondary actions.

For a published tender:

```text
[Clarifications] [Create Addendum] [View Submissions] [Prepare Opening]
```

### More Menu

Move rare, dangerous, or administrative actions into a menu:

```text
[More ▾]
- Cancel tender
- Mark retender required
- Supersede
- View audit trail
- Technical references
```

---

# 4. Do Not Show All Disabled Actions

Do not display every lifecycle action as a disabled button.

Disabled buttons are useful when the user reasonably expects an action to be available and needs to understand why it is blocked.

But showing ten disabled buttons at once creates clutter.

## Better Rule

Only show:

1. actions that are currently available
2. the next blocked action, if it explains what the user must do next
3. rare/admin actions inside a More menu

For example, on a published tender:

```text
[View] [Clarifications] [Create Addendum] [View Submissions] [Prepare Opening] [More ▾]
```

Inside More:

```text
Cancel tender
Mark retender required
Supersede
Evidence export
Technical references
```

Do not show:

```text
Edit draft
Bind STD
Run readiness
Submit for review
Approve publication
Publish
```

Those are past-stage actions. They should be hidden, not disabled.

---

# 5. “Technical References” Are Still Too Prominent

In the latest screenshot, “Technical references” appears immediately under the action area, and then the system shows the gray cards again.

This is still too close to the primary work area.

Technical references should not be in the default detail view.

## Better Placement

Use a small link or button:

```text
[Technical references]
```

Place it in:

- Audit tab
- More menu
- right-side drawer

Do not show technical references immediately under the main action bar.

For a published tender overview, the user should first see:

```text
Key dates
Blockers
Recent activity
Submissions summary
Clarifications/Addenda summary
```

not technical cards.

---

# 6. The Gray Card Grid Still Needs Reduction

The status badges at the top are good:

```text
Lifecycle: Published
STD: Ready
Readiness: Ready
Supplier access: Valid
Blockers: No blockers
```

Because those badges now exist, the gray card grid below is partly redundant.

Current lower cards:

```text
Tender state
STD binding
Readiness
Outputs
Publication snapshot
Timeline
Supplier access
Blockers
```

This is still a diagnostic console.

## Replace with Collapsible Sections

Default overview should show:

```text
Key dates
Submission deadline
Opening scheduled

Operational status
No blockers
Supplier access valid
1 bid submitted

Recent activity
Tender published
Bid submitted
Bid sealed
```

Then hide details under accordions:

```text
[STD and output references]
[Timeline details]
[Technical references]
```

---

# 7. Better Layout for the Selected Tender Detail

The detail pane should be structured like this:

```text
TND-MOH-2029-0007 · B3 Package 24c6
MOH · Open Tender · Goods

[Published] [STD Ready] [Readiness Ready] [Supplier Access Valid] [No Blockers]
Submission: 01 Jun 2026, 19:26 · Opening: 02 Jun 2026, 19:26

Next step
Monitor lifecycle and downstream work.

[View Tender] [Clarifications] [Create Addendum] [View Submissions] [Prepare Opening] [More ▾]

Overview | Preparation | Live Tender | Handoff | Audit

Key dates
Submission deadline        01 Jun 2026, 19:26
Opening scheduled          02 Jun 2026, 19:26

Current activity
Clarifications             5 pending
Addenda                    0
Submissions                1 received

Blockers
No tender-level blockers.
```

That is cleaner and more work-oriented.

---

# 8. What Is Working Well Now

The refactor is moving in the right direction.

Good changes:

- The implementation metadata is gone.
- The lifecycle queues are grouped logically.
- The tender list and detail panel relationship is clearer.
- The selected tender has a stronger identity area.
- Status badges are much better than the old equal-weight gray cards.
- The tab group is much better: `Overview | Preparation | Live Tender | Handoff | Audit`.

That tab grouping is a strong improvement. Keep it.

---

# 9. What to Change Next

In priority order:

1. **Give the left tender list its own scrollbar.**
2. **Make the selected tender header sticky.**
3. **Hide unavailable past-stage actions instead of showing disabled buttons.**
4. **Move rare actions into a More menu.**
5. **Move technical references into Audit or a drawer.**
6. **Replace the lower gray diagnostic cards with operational overview sections.**
7. **Compress the lifecycle queue bar further.**
8. **Reduce tender card height and remove repeated text.**

---

## Direct Assessment

Yes, the left list would be better with a scrollbar.

Yes, the queue commands are better presented now, especially because they are grouped by lifecycle stage. But they still take too much vertica