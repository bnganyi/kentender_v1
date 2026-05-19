# KenTender Compact Queue Bar Refactor Recommendation

This document captures the follow-up recommendation for the Tender Management queue filter area. The latest implementation improved lifecycle grouping, but it reintroduced the original space-usage problem by making the queue area too tall.

The goal of this refactor is to preserve lifecycle clarity while reducing vertical space and returning visual priority to the actual tender workbench.

---

# 1. Current Assessment

The latest version fixed the visual grouping problem, but it overcorrected.

The queue area is now structurally clearer, but spatially too expensive.

The issue is that the queue filter is being treated like a dashboard panel. It should behave like a **compact navigation/filter bar**.

---

# 2. What Went Wrong

The new queue design uses:

- large outer container
- inner bordered group cards
- separate row for `All / My Work`
- separate row for the first three lifecycle groups
- separate full-width row for `Closing & Handoff`
- large vertical padding inside every group

That makes the queues consume nearly the same visual weight as the actual tender workbench. For this screen, that is the wrong tradeoff.

The lifecycle grouping should help orientation, not become the primary content.

---

# 3. Recommended Fix: Collapse Queues into a Compact Two-Line Lifecycle Bar

Use this structure:

```text
[All 13] [My Work]   Preparation: [Draft 3] [Doc incomplete 3]   Review: [Review 0] [Returned 0] [Approved 2]
Live: [Published 5] [Clarifications 5] [Addenda 0]   Closing: [Closing soon 0] [Opening ready 0] [Closed 0] [Evaluation ready 0] [Cancelled 0]
```

This keeps grouping, but removes the card-like bulk.

The visual distinction should come from **text treatment**, not boxes.

---

# 4. Better Target Layout

```text
Tender Management                                  [My Actions] [Evidence Export] [New Tender]
Create, publish, amend, close, and hand off governed tenders through one workbench.

[All 13] [My Work]

Preparation  [Draft 3] [Doc incomplete 3]   Review  [Review 0] [Returned 0] [Approved 2]   Live  [Published 5] [Clarifications 5] [Addenda 0]
Closing      [Closing soon 0] [Opening ready 0] [Evaluation ready 0] [Closed 0] [Cancelled 0]

────────────────────────────────────────────────────────────────────────────────
Tender list                  Detail panel
```

This should occupy about **80–110px**, not 200px or more.

---

# 5. Remove the Group Boxes

The current grouped cards look neat, but they cost too much vertical space.

Do **not** use this:

```text
┌ Preparation ─────────────────────┐
│ [Draft 3] [Doc incomplete 3]     │
└──────────────────────────────────┘
```

Use this instead:

```text
Preparation  [Draft 3] [Doc incomplete 3]
```

or:

```text
PREP  [Draft 3] [Doc incomplete 3]
```

The stage label only needs to orient the user. It does not need a container.

---

# 6. Use Compact Stage Labels

Recommended label options:

```text
Prep
Review
Live
Closing
```

or, slightly more formal:

```text
Preparation
Review
Live Tender
Closing
```

For a government-facing procurement system, prefer:

```text
Preparation
Review
Live Tender
Closing
```

Avoid full `Closing & Handoff` in the queue bar. Handoff is already a tab and downstream phase. In this top filter area, `Closing` is sufficient.

---

# 7. Recommended Visual Style

Use this hierarchy:

```css
.queue-bar {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
}

.queue-scope-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.queue-stage-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  align-items: center;
}

.queue-stage {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.queue-stage-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.queue-chip {
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
}
```

The important part: **no nested cards**.

---

# 8. Make Secondary and Zero-Count Queues Less Prominent

The current implementation shows every queue with the same spatial presence. But `0` queues should not dominate.

Use this rule:

- active / selected queue: black
- nonzero queue: normal chip
- zero-count queue: ghost chip or plain muted text

Example:

```text
Preparation  [Draft 3] [Doc incomplete 3]
Review       Review 0 · Returned 0 · [Approved 2]
Live Tender  [Published 5] [Clarifications 5] Addenda 0
Closing      Closing soon 0 · Opening ready 0 · Closed 0 · Evaluation ready 0 · Cancelled 0
```

Or, if all queues should remain clickable:

```text
Preparation  [Draft 3] [Doc incomplete 3]
Review       [Review 0] [Returned 0] [Approved 2]
Live Tender  [Published 5] [Clarifications 5] [Addenda 0]
Closing      [Closing soon 0] [Opening ready 0] [Closed 0] [Evaluation ready 0] [Cancelled 0]
```

In either case, style zero-count chips with lower contrast.

---

# 9. Best Compact Version for the Current Screen

Given the width shown in the screenshot, use this:

```text
[All 13] [My Work]

Preparation  [Draft 3] [Doc incomplete 3]     Review  [Review 0] [Returned 0] [Approved 2]     Live  [Published 5] [Clarifications 5] [Addenda 0]
Closing      [Closing soon 0] [Opening ready 0] [Evaluation ready 0] [Closed 0] [Cancelled 0]
```

This gives grouping, keeps the selected state obvious, and avoids large containers.

---

# 10. Alternative: Move Queues into the Left Panel

This is worth considering if the queue list keeps growing.

The top queue area could be reduced to:

```text
[All 13] [My Work] [Published 5 ▾]
```

Then the left panel contains the lifecycle filter:

```text
Tender list
[Search...]

Lifecycle
Preparation
  Draft 3
  Doc incomplete 3

Review
  Review 0
  Returned 0
  Approved 2

Live
  Published 5
  Clarifications 5
  Addenda 0

Closing
  Closing soon 0
  Opening ready 0
  Evaluation ready 0
  Closed 0
  Cancelled 0
```

This is a good pattern if queue filtering is frequently used. But it makes the left panel denser.

For now, keep the queues top-level but compress them.

---

# 11. Direct Recommendation

Do not use grouped queue cards.

Use a **compact, inline grouped queue bar**:

```text
[All 13] [My Work]
Preparation [Draft 3] [Doc incomplete 3] · Review [Review 0] [Returned 0] [Approved 2] · Live [Published 5] [Clarifications 5] [Addenda 0]
Closing [Closing soon 0] [Opening ready 0] [Evaluation ready 0] [Closed 0] [Cancelled 0]
```

Target height: **maximum 96px**.

That will preserve the lifecycle clarity without pushing the actual tender workbench too far down.

