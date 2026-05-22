# Workspace Pattern Rollout Matrix

## Goal
Prevent repeated UX regressions by enforcing a shared workspace contract across KenTender modules.

## Contract Scope
- Master-detail workspace structure
- List selection updates detail without list scroll jump
- No loading flash/flicker when switching tabs or records
- Native Frappe typography and spacing baseline
- Stable `data-testid` selectors for list/detail/tabs

## Rollout Status
- Strategy: locked (`strategy-pattern-lock.spec.ts`)
- Budget: pending contract spec
- DIA: pending contract spec
- Procurement/TM2: partial coverage (`tm2-workbench-list-scroll.spec.ts`)

## Required Pattern Gate
Run `make -C apps/kentender_v1 ui-workspace-pattern-gate` before marking workspace UX work done.

## Adoption Steps For New Module
1. Add module smoke spec under `tests/ui/smoke/<module>/`.
2. Add module workspace contract spec (scroll + anti-flicker + detail-selection).
3. Ensure required testids exist and are stable.
4. Add spec to `ui-workspace-pattern-gate`.
5. Validate visually with MCP browser tools.
