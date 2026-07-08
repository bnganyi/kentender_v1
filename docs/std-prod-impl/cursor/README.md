# KenTender Cursor Rules Pack

Rules for the **STD Engine production** module (Official Standard Tender Document Library).

## Installed location (active)

Rules are installed at the **bench root** for Cursor to load automatically:

```
frappe-bench/.cursor/rules/
  kentender-std-prod-impl.mdc          # bootstrap — read first
  kentender-std-prod-001-project-architecture.mdc
  kentender-std-prod-002-procurement-governance.mdc
  kentender-std-prod-003-domain-modeling-and-storage.mdc
  kentender-std-prod-004-code-quality-and-scope-control.mdc
  kentender-std-prod-005-testing-and-smoke-contracts.mdc
  kentender-std-prod-006-task-protocol.mdc
  kentender-std-prod-007-import-export-rendering.mdc
  kentender-std-prod-008-security-audit-evidence.mdc
  kentender-std-prod-009-ui-ux-government-workflows.mdc
  kentender-std-prod-010-documentation-status-discipline.mdc
```

Scoped globs load these rules when work touches `docs/std-prod-impl/` or related STD/tender_management code paths. **`kentender-v1.mdc`** also points here for STD Engine production tasks.

## Canonical source (edit here)

This folder remains the **editable source of truth**:

- `AGENTS.md` — agent execution instructions
- `CURSOR_RULES_ALL_IN_ONE.md` — human-readable rollup
- `.cursor/rules/*.mdc` — individual rule files

When rules change, update files here, then re-sync to `frappe-bench/.cursor/rules/kentender-std-prod-*.mdc` (preserve scoped `globs` / `alwaysApply: false` frontmatter on the bench copies).

## Recommended usage

1. Keep these rules committed to the repository.
2. Before each implementation task, give Cursor one bounded task and the relevant context documents only.
3. Require Cursor to produce a plan before editing files when the task touches governance, lifecycle, storage, or rendering.
4. Require tests, smoke-contract checks, and status doc updates before accepting a task.
5. Do not ask Cursor to implement broad modules in one prompt.

The rules intentionally protect the STD Engine from shortcuts that would compromise legal traceability, lifecycle governance, immutability, auditability, and future support for multiple Standard Tender Documents.
