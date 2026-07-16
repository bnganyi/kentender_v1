# IT Tender Configuration Wizard UX Refactor Charter

## 1. Purpose

This refactor exists to make the IT Tender Configuration Wizard simple enough for procurement users to configure a tender without feeling they are operating a legal, technical, pricing, evaluation, and contract console at the same time.

The issue is not that the legal model is unnecessary. The issue is that the user interface has exposed too much of it.

## 2. Scope

This refactor applies to **all IT Tender Wizard screens**, not only the screens where problems have already appeared.

Screens in scope:

1. Dashboard
2. Tender Configuration Overview
3. Tender Profile
4. Tender Data Sheet
5. IT Requirements
6. Implementation Schedule
7. System Inventory
8. Price Schedule
9. Evaluation Setup
10. Forms & Evidence
11. SCC / Contract Carry-Forward
12. Validation Report
13. Review & Approval
14. Final Tender Preview
15. Publication Readiness

No screen is exempt from simplification.

## 3. Required Sequence

Yes, we will follow the new approach:

1. **User journey** — what the user is trying to achieve.
2. **Decision map** — the single decision each screen supports.
3. **Screen ownership matrix** — what each screen owns, references, and must not show.
4. **UX review** — aggressively remove fields, panels, statuses, and cross-links that do not support the screen decision.
5. **Only then** produce or revise the PRD, domain model, API contract, Stitch prompt, and Cursor prompt.

No further screen implementation should proceed until the screen has passed this sequence.

## 4. Core Principle

Each screen must help the user make **one clear decision**.

If a field does not support that decision, it must be removed from the main screen, moved to the owning screen, or hidden behind progressive disclosure.

## 5. Design Direction

Design from the user decision, not from the STD structure, database model, or downstream consumers.

Correct path:

```text
User goal
→ User decision
→ Minimal fields
→ System derives downstream outputs
```

Wrong path:

```text
STD section
→ Every possible object
→ Every downstream linkage
→ Everything visible everywhere
```

## 6. Non-Negotiable Rules

1. One screen, one primary decision.
2. One screen, one primary owned object.
3. No magical values.
4. No unexplained read-only fields.
5. Template-prefilled values are editable unless legally locked.
6. References are links, not embedded workspaces.
7. Validation is calm and minimal on individual screens.
8. Legal, audit, and technical details stay out of the default view.
9. If a field is useful only to another module, remove it from the current screen.
10. Usability beats theoretical completeness in the visible UI.

## 7. Field Source Rule

Every displayed value must be one of these:

| Source Type | UI Behavior |
|---|---|
| User-entered | Editable |
| Template-prefilled | Editable; Reset to Template available |
| Derived | Read-only with source explanation |
| Owned elsewhere | Read-only with link to owning screen |
| STD-locked | Read-only with legal/source explanation |
| Not configured | Show `Not configured`; offer configure action only if this screen owns it |

## 8. Refactor Method Per Screen

For each screen, produce a concise refactor note answering:

1. What is the user trying to do?
2. What single decision does the screen support?
3. What object does the screen own?
4. What fields are editable here?
5. What references may be shown lightly?
6. What must be removed?
7. What validation is shown locally?
8. What is hidden in drawer/details/audit views?
9. What should Stitch build?
10. What should Cursor implement?

## 9. Definition of Done

A screen is refactored only when:

- its purpose is obvious in under ten seconds;
- it supports one primary decision;
- every editable field is owned by that screen;
- every read-only field explains source and reason;
- no hardcoded realistic values are shown;
- references are lightweight;
- validation is minimal;
- advanced/audit/legal-engine detail is hidden by default;
- the screen feels like tender configuration, not system administration.

## 10. Operating Instruction

From now on, PRDs and prompts must be shorter, sharper, and more restrictive.

They must tell Stitch and Cursor what **not** to build as clearly as what to build.

