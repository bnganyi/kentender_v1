---
trigger: always_on
description: Lock shared workspace UX patterns across modules.
---

Workspace pattern lock (Strategy, Budget, DIA, and future workbenches):

- Preserve list scroll position when selecting a record.
- Update detail panel without loading flicker or full-pane wipe.
- Switching rows must keep the same detail shell node mounted; only patch values/panel content in place.
- Do not re-show generic detail loading placeholders when changing selection and a detail shell is already mounted.
- Keep active tab host/wrapper stable during first row selection when current tab has not changed.
- Drawer/iframe edit forms must suppress sidebar/chrome before first visible paint.
- Guard async mounts against stale responses (token/request id discipline).
- Keep muted inline status style in list rows unless module contract says otherwise.
- Maintain native Frappe spacing/typography rhythm; avoid over-compacting core text.
- Keep stable `data-testid` selectors for list, detail, tabs, and critical actions.

Before marking UX work done:

1) Run Playwright workspace contract tests.
2) Run module smoke tests.
3) Validate behavior in MCP browser tools.
