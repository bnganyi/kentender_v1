# G0-004 Main Procurement Shell Confirmation

Date: 2026-05-26  
Source inputs: `G0-001_current_ui_inventory_evidence.md`, `G0-002_delete_refactor_list.md`, `G0-003_route_plan_confirmation.md`

## 1) Shell containment verdict

Verdict: **Partial (architecture compliant, IA content still non-compliant)**.

- Planning routes currently run inside the main Procurement shell and retain Procurement rail context.
- Current Planning IA content still needs reset alignment (missing `Plans`, persistent `Planning Evidence`) as recorded in G0-001/G0-002/G0-003.
- This gate confirms shell containment behavior, not full P5A IA completion.

## 2) Criteria for “inside main Procurement shell”

| Criterion | Current status | Evidence pointer |
|---|---|---|
| Planning remains under Procurement module navigation (not standalone app shell) | Pass | `workspace_sidebar/procurement.json` shows Planning nested under Procurement |
| Planning routes resolve under `/desk/procurement-planning*` | Pass | G0-001 route matrix + `pp2_planning_router.js` root path handling |
| Sidebar fast-path maps Planning route keys to Procurement rail | Pass | `setup/workspace_permissions.py` `_KT_WORKSPACE_TO_SIDEBAR` |
| Module route registry treats planning paths as Procurement context | Pass | `kt_module_registry.js` + `module_registry.py` route prefixes |
| No active standalone `pp2-planning` workspace path as primary shell | Pass | Navigation hooks remove retired `pp2-planning`; runtime uses Procurement nested surfaces |
| Planning child IA equals final reset 5-item set | Fail (known) | G0-001/G0-002/G0-003: missing `Plans`, persistent `Planning Evidence` |

## 3) Route x shell matrix (current)

| Route | Procurement rail context retained | Planning nested under Procurement | Notes |
|---|---|---|---|
| `/desk/procurement-planning` | Yes | Yes | Shell mounted via planning router in Procurement context |
| `/desk/procurement-planning/approved-demands` | Yes | Yes | Nested route in same Procurement rail |
| `/desk/procurement-planning/plans` | Yes | Yes | Currently falls back to Planning Home route handling |
| `/desk/procurement-planning/packages` | Yes | Yes | Nested packages route; content model superseded but shell context retained |
| `/desk/procurement-planning/packages/<package_code>` | Yes | Yes | Currently falls back to Planning Home route handling |
| `/desk/procurement-planning/releases` | Yes | Yes | Nested releases route in Procurement rail |

## 4) Negative confirmation (standalone shell anti-pattern check)

Confirmed for current architecture:

- No requirement path uses a separate `pp2-planning` standalone shell as the primary runtime context.
- Planning routes are wired through Procurement sidebar/registry/fast-path mappings.
- Shell preservation logic is explicit in route/boot mappings (Procurement rail remains owner).

Known remaining reset deltas (not shell-containment failures):

- Persistent ordinary `Planning Evidence` submenu remains (to be removed in P5A-004).
- Missing persistent `Plans` submenu route implementation (to be completed in P5D/P5A alignment).

## 5) Code ownership map for shell behavior

| Concern | Owner file(s) |
|---|---|
| Planning nested route mount and shell injection | `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js` |
| Procurement rail child links and Planning nesting | `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json` |
| Boot-time sidebar fast-path keys for planning routes | `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py` |
| Module route context (JS) | `apps/kentender_v1/kentender_core/kentender_core/public/js/kt_module_registry.js` |
| Module route context (Python mirror) | `apps/kentender_v1/kentender_core/kentender_core/module_registry.py` |

## 6) Downstream linkage

This confirmation feeds:

- `P5A-002` (preserve main Procurement shell after reset refactor)
- `P5A-003` (exact five Planning child links)
- `P5A-004` (remove persistent Planning Evidence submenu)

## 7) Tracker-format evidence block

Implementation Evidence:
- Code path(s):
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py`
  - `apps/kentender_v1/kentender_core/kentender_core/public/js/kt_module_registry.js`
  - `apps/kentender_v1/kentender_core/kentender_core/module_registry.py`
- Component/template path(s): Router shell mount + sidebar/registry configuration listed above.
- Route path(s): `/desk/procurement-planning*` planning route family (home, approved-demands, plans, packages, package-detail path, releases).
- API/service path(s), if applicable: N/A for shell confirmation gate.

Test Evidence:
- Test path(s):
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-sidebar-p5-001.spec.ts`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_workspace_sidebar_fastpath.py`
- Command(s) run: N/A for this G0 documentation gate.
- Result: N/A for this G0 documentation gate.

UI Proof:
- Screenshot(s), if UI row:
  - Route proof and shell behavior documented from G0-001 evidence set and route/shell code ownership.
  - G0-001 screenshot index referenced in source input artifact.
- Route: `/desk/procurement-planning*`
- Role: Administrator (source evidence baseline)
- Selected queue/item: N/A (shell gate)
- Primary action visible: N/A (shell gate)

Review Notes:
- Planning is confirmed to remain under Procurement shell architecture.
- IA content remains partial and is tracked for P5A/P5D corrections (not a blocker for G0-004 evidence submission).
