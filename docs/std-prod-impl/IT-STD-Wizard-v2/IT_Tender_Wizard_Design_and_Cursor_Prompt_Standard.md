# IT Tender Wizard Design and Cursor Prompt Standard

## 1. Purpose

This standard governs all future Stitch and Cursor prompts for the IT Tender Wizard.

Its purpose is to stop PRDs and prompts from reintroducing complexity, magical values, unexplained read-only fields, and cross-screen sprawl.

## 2. Required Sequence

Use this sequence for every screen:

1. User journey
2. Decision map
3. Screen ownership matrix
4. UX simplification review
5. PRD / domain / API / Stitch / Cursor prompt

Do not skip directly to PRD or implementation prompt.

## 3. Required Prompt Sections

Every Stitch or Cursor prompt must include:

```text
Screen name:
User goal:
Single user decision:
Primary object owned:
STD/workflow anchor:
Editable fields:
Read-only references:
Forbidden fields/behaviors:
Default layout:
Drawer/details behavior:
Validation behavior:
Actions:
Complexity removal rules:
```

If any section is missing, the prompt is not ready.

## 4. Prompt Rules

### 4.1 Start with the user decision

Good:

```text
The user decides what bidders must supply or satisfy.
```

Bad:

```text
The screen manages requirements, evidence, scoring, acceptance, contract carry-forward, and validation.
```

### 4.2 Define ownership

Every prompt must say what the screen owns.

Example:

```text
Primary object owned: IT Requirement Item.
```

### 4.3 Separate editable fields from references

Prompts must separate:

```text
Editable here
```

from:

```text
Displayed as source-backed reference only
```

### 4.4 Forbid wrong content explicitly

Prompts must say what not to build.

Example:

```text
Do not show scoring marks, score percentages, bidder scores, actual evaluation results, or contract approval controls on IT Requirements.
```

### 4.5 No magical values

Do not hardcode realistic values such as:

```text
2,500 concurrent users
42 locations
RBAC / MFA
On-Premise
```

Show source-backed values or `Not configured`.

### 4.6 No unexplained read-only fields

Every read-only field must explain why.

Examples:

```text
Source: Evaluation Setup. Edit in Evaluation Setup.
```

```text
Source: Bound STD Package. Locked because this is standard text.
```

### 4.7 Keep validation calm

Use simple local statuses:

```text
Complete
Missing required field
Needs review
Warnings remain
```

Full findings belong in Validation Report.

### 4.8 Use progressive disclosure

Default view: simple configuration.

Drawer: details, source labels, secondary references.

Audit/details: legal traceability and technical metadata.

Do not put all layers on the main screen.

## 5. Field Source Model

Every displayed field must carry this internal model:

```text
field_name
value
source_type
source_object
owner_screen
editable
read_only_reason
edit_target
```

Allowed source types:

```text
USER_ENTERED
TEMPLATE_PREFILLED
DERIVED
OWNED_ELSEWHERE
STD_LOCKED
NOT_CONFIGURED
```

## 6. Standard Stitch Prompt Skeleton

```text
Design [Screen Name] for the KenTender IT Tender Configuration Wizard.

User goal:
[one sentence]

Single user decision:
[one decision]

Primary object owned:
[object]

STD/workflow anchor:
[anchor]

Editable fields:
[list only fields owned by this screen]

Read-only references:
[list only lightweight source-backed references]

Forbidden fields/behaviors:
[list]

Default layout:
Simple main work area, lightweight guidance, bottom actions.
Do not show competing workspaces.

Drawer/details behavior:
Use drawer for secondary detail, sources, and references.

Validation behavior:
Show local completeness only. Full findings belong in Validation Report.

Actions:
[list]

Complexity removal rules:
Remove anything that does not support the screen's single decision.
Hide legal/audit/technical metadata from the default view.
```

## 7. Standard Cursor Prompt Skeleton

```text
Refactor [Screen Name] in the KenTender IT Tender Configuration Wizard.

Goal:
Make this screen support one decision: [decision].

Primary object owned:
[object]

Editable fields owned by this screen:
[list]

Read-only references allowed:
[list]

Forbidden fields and behaviors:
[list]

Implement field source model for every displayed value:
- source_type
- source_object
- owner_screen
- editable
- read_only_reason
- edit_target

Do not render unexplained read-only fields.
Do not render hardcoded magical values.
If a value has no configured source, show Not configured.

Use progressive disclosure:
- default view: simple configuration
- drawer: details and source references
- audit/details: technical trace only when explicitly opened

Validation:
Show only local completeness status.
Deep validation findings belong to Validation Report.

Expected result:
The screen is simpler, more focused, and clearly owned.
```

## 8. Review Checklist

Before handing over a prompt, confirm:

1. The screen has one user decision.
2. The screen owns one primary object.
3. Editable fields are limited to that object.
4. References are lightweight.
5. Forbidden content is explicit.
6. No magical values are introduced.
7. Read-only values explain source and reason.
8. Validation is minimal.
9. Technical/legal/audit metadata is hidden by default.
10. The screen can be understood in under ten seconds.

## 9. Operating Rule

Concise prompts are preferred.

A long prompt is acceptable only when it removes ambiguity. It is not acceptable when it adds extra product scope.

