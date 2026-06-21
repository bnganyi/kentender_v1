# KenTender PP2 P5-003 Journey Context Header UX Audit

This document audits only the current Procurement Planning `P5-003 ModuleJourneyContextHeader` implementation.

It intentionally does **not** recommend implementing Planning Home content, queues, dashboards, package cards, or downstream features. Those belong to later tickets. The purpose here is to keep P5-003 tight, testable, and aligned with the usability goal: make the application less intimidating and easier to understand.

---

# 1. Scope Boundary

## In Scope for P5-003

P5-003 should deliver only the shared journey context header for Procurement Planning surfaces.

It should show:

- the business object / journey name
- a compact state summary
- one clear next-action sentence or status sentence
- a primary navigation/action link if applicable
- an optional technical-details disclosure

## Out of Scope for P5-003

Do not implement or redesign:

- Planning Home dashboard cards
- Approved Demands queue contents
- Packages workspace contents
- Released to Tender page contents
- Planning Evidence page contents
- readiness panels
- package creation flow
- release flow
- review/approval screens
- home-page summaries
- placeholder dashboard cards

Those belong to later tickets. Cursor must not implement ahead.

---

# 2. Current Screen Assessment

The current implementation shows a journey context card with useful data, but the default presentation is too technical and too text-heavy.

Current visible content includes:

```text
District Hospital Renovation Works
Business view
Current step: Procurement Planned
Previous step: Approved demand included in procurement plan
Next step: Tender Management consumed the package / continue in Tender Management
Technical details
Stage key: planning_inclusion | Journey code: JRN-MOH-2026-001 | Inclusion handoff: PLANINCL-MOH-2026-001 | Release handoff: PKGREL-MOH-2026-001
```

This has two problems:

1. **The ordinary user still has to read too much.**
   - The header is supposed to orient the user quickly.
   - It currently requires careful reading to understand what happened and what to do.

2. **Technical details are visible by default.**
   - Stage keys, journey codes, inclusion handoff codes, and release handoff codes are not default business UI.
   - They should be available only after explicit expansion.

---

# 3. Required UX Direction

The header should be a **compact orientation strip**, not a mini report.

It should answer only three questions:

```text
What is this?
Where is it in the journey?
What should I do next?
```

Do not show a long explanation in the header.

Do not expose technical IDs by default.

---

# 4. Recommended Header Content

Use a compact business-first layout:

```text
District Hospital Renovation Works
Procurement planned · Tender Management has consumed the released package

[Open Procurement Journey] [Open Tender Management]
[Show technical details]
```

If only one action is available:

```text
District Hospital Renovation Works
Procurement planned · Continue in Tender Management

[Open Procurement Journey]
[Show technical details]
```

If no action is available:

```text
District Hospital Renovation Works
Procurement planned · No action required in Planning

[Open Procurement Journey]
[Show technical details]
```

This is enough for P5-003.

---

# 5. Recommended Visual Structure

The header should have three compact zones:

```text
┌────────────────────────────────────────────────────────────────────┐
│ District Hospital Renovation Works                   [Open Journey] │
│ Procurement planned · Continue in Tender Management                 │
│ Show technical details                                              │
└────────────────────────────────────────────────────────────────────┘
```

## Visual Rules

- Title should be the strongest text.
- State line should be short and muted.
- Primary action should be on the right.
- Technical disclosure should be small and secondary.
- Header height should stay compact.
- Avoid multi-line paragraphs.
- Avoid “Previous step / Current step / Next step” labels unless necessary.

---

# 6. What to Remove from Default Header

Remove these from default visible state:

```text
Technical details
Stage key: planning_inclusion
Journey code: JRN-MOH-2026-001
Inclusion handoff: PLANINCL-MOH-2026-001
Release handoff: PKGREL-MOH-2026-001
```

Also avoid visible labels like:

```text
Business view
Current step:
Previous step:
Next step:
```

Those labels add cognitive load. The user should not need to parse a lifecycle report just to understand the page.

---

# 7. Technical Details Disclosure

Technical details should be hidden by default behind a clear disclosure:

```text
Show technical details
```

When expanded, show:

```text
Technical details
Stage key: planning_inclusion
Journey code: JRN-MOH-2026-001
Inclusion handoff: PLANINCL-MOH-2026-001
Release handoff: PKGREL-MOH-2026-001
```

This satisfies audit/debug needs without intimidating ordinary users.

Do not label the collapsed control simply as `Technical details` if that makes it look like the section is already open. Use an action label:

```text
Show technical details
Hide technical details
```

---

# 8. Recommended Copy Rules

Use short state sentences.

## Good

```text
Procurement planned · Continue in Tender Management
```

```text
Released to Tender · Awaiting Tender Management consumption
```

```text
Included in plan · Package not created yet
```

```text
Package in review · Waiting for planning approval
```

## Avoid

```text
Previous step: Approved demand included in procurement plan
Next step: Tender Management consumed the package / continue in Tender Management
```

This is accurate but too wordy for a header.

---

# 9. State Copy Examples for P5-003

Cursor should use a small mapping table rather than generating free text.

| Business State | Header State Line |
|---|---|
| Approved demand available | `Approved demand · Ready for planning inclusion` |
| Included in plan | `Included in plan · Package not created yet` |
| Package draft | `Package draft · Complete package details` |
| Package in review | `Package in review · Waiting for planning approval` |
| Ready for release | `Ready for release · Release package to Tender Management` |
| Released to tender | `Released to Tender · Awaiting Tender Management consumption` |
| Consumed by Tender Management | `Procurement planned · Continue in Tender Management` |
| Blocked | `Blocked · Resolve the listed issue before continuing` |

For the current screenshot, use:

```text
Procurement planned · Continue in Tender Management
```

or, if the release has been fully consumed:

```text
Procurement planned · Tender Management has consumed the released package
```

Prefer the shorter version unless the distinction matters.

---

# 10. Button Rules

The header should not become an action toolbar.

Allowed P5-003 header actions:

```text
Open Procurement Journey
Open Tender Management / Open Tender
Show technical details
```

Do not add:

```text
Create package
Run readiness
Submit review
Release to tender
View all evidence cards
Resolve blocker
```

Those actions belong to later workflow surfaces, not the P5-003 journey context header.

---

# 11. P5-003 Acceptance Criteria

P5-003 passes when:

1. The header is visible on the Procurement Planning shell.
2. The header shows the journey/business title.
3. The header shows one concise business-readable state line.
4. The header shows at most one primary action plus optional secondary navigation.
5. Technical stage keys and handoff codes are hidden by default.
6. Technical details are available only through `Show technical details`.
7. The header does not include implementation placeholder text.
8. The header does not introduce Planning Home dashboard content or other later-ticket content.
9. The default header can be understood in under five seconds.
10. Automated or manual evidence proves technical codes are absent before expansion and present only after expansion.

---

# 12. P5-003 Rework Required

The current implementation should be marked:

```text
P5-003: Rework Required
```

Reasons:

1. Technical details are visible by default.
2. The header is too text-heavy for a user-orientation component.
3. The labels `Current step`, `Previous step`, and `Next step` make the header feel like a lifecycle report.
4. Ordinary users are forced to read too much before they can understand what the page means.
5. The header does not yet meet the compact business-first visibility requirement.

---

# 13. Exact Cursor Instruction

Use this instruction directly:

```text
Rework only P5-003 ModuleJourneyContextHeader.
Do not implement Planning Home dashboard content, queue bodies, package flows, readiness panels, or any later-ticket UI.

Replace the current text-heavy journey header with a compact business-first orientation strip:

Title: District Hospital Renovation Works
State line: Procurement planned · Continue in Tender Management
Primary action: Open Procurement Journey
Optional secondary action: Open Tender Management / Open Tender, only if the target route is already available
Disclosure: Show technical details

Hide all technical fields by default, including:
- stage key
- journey code
- inclusion handoff code
- release handoff code

Show those fields only after the user expands Show technical details.

Do not show implementation placeholder text to users.
Do not add any new Planning Home content under this ticket.
```

---

# 14. Final Recommendation

The earlier audit correctly identified technical leakage, but the correction must go further: the header should not merely hide technical details; it should also become much shorter.

The target is:

```text
District Hospital Renovation Works
Procurement planned · Continue in Tender Management
[Open Procurement Journey]
[Show technical details]
```

That is the level of simplicity needed for P5-003.

Anything beyond that risks scope creep and should be deferred to the correct later ticket.

