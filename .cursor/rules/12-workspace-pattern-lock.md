---
trigger: always_on
description: Lock shared workspace UX patterns across modules.
---

Workspace pattern lock (Strategy, Budget, DIA, and future workbenches):

- Preserve list scroll position when selecting a record.
- Update detail panel without loading flicker or full-pane wipe.
- Guard async mounts against stale responses (token/request id discipline).
- Keep muted inline status style in list rows unless module contract says otherwise.
- Maintain native Frappe spacing/typography rhythm; avoid over-compacting core text.
- Keep stable `data-testid` selectors for list, detail, tabs, and critical actions.

Before marking UX work done:

1) Run Playwright workspace contract tests.
2) Run module smoke tests.
3) Validate behavior in MCP browser tools.
