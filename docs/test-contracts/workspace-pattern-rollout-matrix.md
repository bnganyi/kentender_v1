# Workspace Pattern Rollout Matrix

## Goal
Prevent repeated UX regressions by enforcing a shared workspace contract across KenTender modules.

## Contract Scope
- Master-detail workspace structure
- List selection updates detail without list scroll jump
- No loading flash/flicker when switching tabs or records
- First row selection keeps the current tab host stable (no wrapper remount when tab is unchanged)
- Drawer/iframe form loads suppress sidebar/chrome before first visible paint
- Native Frappe typography and spacing baseline
- Stable `data-testid` selectors for list/detail/tabs
- Visual hierarchy contract (filters != tabs != actions != row links)

## Rollout Status
- Strategy: locked (`strategy-pattern-lock.spec.ts`)
- Budget: locked (`budget-pattern-lock.spec.ts`)
- DIA: locked (`dia-pattern-lock.spec.ts`)
- Procurement/TM2: partial coverage (`tm2-workbench-list-scroll.spec.ts`)

## Required Pattern Gate
Run `make -C apps/kentender_v1 ui-workspace-pattern-gate` before marking workspace UX work done.

## Adoption Steps For New Module
1. Add module smoke spec under `tests/ui/smoke/<module>/`.
2. Add module workspace contract spec (scroll + anti-flicker + detail-selection + visual hierarchy + drawer preload check when module uses iframe/drawer forms).
3. Ensure required testids exist and are stable.
4. Add spec to `ui-workspace-pattern-gate`.
5. Validate visually with MCP browser tools.

## Frappe Fidelity Guardrail
- Do not override global `font-family` for workspace shells.
- Keep typography and color tied to Frappe tokens (`--text-color`, `--text-muted`, `--border-color`).
- Reserve strongest solid action styling for page-level primary action only.
- Primary tabs must not use black-filled pills; prefer underline/nav treatment.
- Row actions should remain low emphasis (link-style), not button-dominant.
