# G0-002 Delete/Refactor List (Pre-Coding Gate)

Date: 2026-05-26  
Source baseline: `G0-001_current_ui_inventory_evidence.md`  
Scope: Planning UI reset pre-coding only (no implementation in this gate)

## 1) Purpose and decision rules

This artifact identifies exactly what current PP2 Planning UI behavior must be removed, hidden/deferred, refactored, relocated, or retained before reset implementation phases (P5A-P5H).  

Classification used:
- `Remove`: delete superseded default UI behavior/path.
- `Hide/Defer`: keep capability but not in ordinary default views.
- `Refactor`: replace existing behavior with reset workbench pattern.
- `Relocate`: move behavior to contextual Evidence/Technical/Audit surfaces.
- `Retain`: keep as-is because it supports reset or backend rigor.

Precedence used: tracker > reset contract > wireframe > backend/domain.

## 2) File/component mapped action inventory

| ID | Current pattern / violation | Action | File(s) and symbol(s) | Replacement target | No-go refs | Risk |
|---|---|---|---|---|---|---|
| G0-002-001 | Packages route defaults to handoff stack as primary content | Remove + Refactor | `public/js/pp2_planning_router.js`: `mountPlanningHandoffStack()`, `buildHandoffCardsFromDetail()`, `bindHandoffOpenLinks()`, `mount()` packages branch | P5D packages workbench (`pp2-work-list` + selected summary panel) | `PP2-P5-NG-002`, `PP2-P5-NG-012` | High |
| G0-002-002 | Implementation-stage stub copy shown on active screens | Remove | `public/js/pp2_planning_router.js`: `renderSurfaceShellStub()` copy strings | Real workbench empty states (P5B/P5C/P5D) | `PP2-P5-NG-007` | Medium |
| G0-002-003 | Right panel shows implementation-stage next-action shell copy | Remove + Refactor | `public/js/pp2_planning_router.js`: `ensurePrimaryWorkspaceShell()` (`pp2-primary-next-action-panel`) | Selected summary panel in main workbench flow | `PP2-P5-NG-007`, `PP2-P5-NG-012` | Medium |
| G0-002-004 | Persistent Planning Evidence surface in Planning nav | Remove | `public/js/pp2_planning_router.js`: `SURFACES.evidence`, `SURFACE_LABELS.evidence`, `readSurfaceSlug()`, `normalizeChildLinkRoutes()` | Contextual View Evidence/Evidence Drawer only | `PP2-P5-NG-003` | High |
| G0-002-005 | Planning submenu includes Planning Evidence and misses Plans | Refactor | `workspace_sidebar/procurement.json` child links under Procurement Planning section | Exact 5-item reset IA: Home, Approved Demands, Plans, Packages, Released | `PP2-P5-NG-003`, reset P5A-003 | High |
| G0-002-006 | Route registry still treats `/procurement-planning/evidence` as ordinary planning surface | Remove + Refactor | `kentender_core/public/js/kt_module_registry.js` (`routePrefixes`), `kentender_core/module_registry.py` (`route_prefixes`) | Keep planning route prefixes for reset IA and package detail only | `PP2-P5-NG-003`, `PP2-P5-NG-012` | Medium |
| G0-002-007 | Boot fast-path mapping includes evidence as ordinary planning route | Refactor | `setup/workspace_permissions.py`: `_KT_WORKSPACE_TO_SIDEBAR` keys `procurement-planning/evidence`, `evidence`; test list in fastpath tests | Route mappings aligned to 5-item IA + contextual evidence entry points | `PP2-P5-NG-003` | Medium |
| G0-002-008 | No dedicated `plans` route slug; `/plans` falls back to home | Refactor | `public/js/pp2_planning_router.js`: `readSurfaceSlug()`, `SURFACES`, `SURFACE_LABELS` | Implement plans route and selector contract (`pp2-plans-page`) | reset P5D-001, G0-003 dependency | Medium |
| G0-002-009 | Path-style package detail `/packages/<package_code>` not active | Refactor | `public/js/pp2_planning_router.js`: route parsing/mount flow | Implement contextual package detail route per P5E | reset P5E-001, G0-003 dependency | Medium |
| G0-002-010 | Legacy alternative renderer present with handoff-heavy/default technical patterns | Remove (after migration/rewrite of tests) | `public/js/procurement_planning_workspace.js` (entire file; not loaded in `hooks.py`) | Single canonical planning renderer path in router/workbench | `PP2-P5-NG-002`, `PP2-P5-NG-012` | Medium |
| G0-002-011 | Dominant journey context header mounted by default on all surfaces | Hide/Defer + Relocate | `public/js/pp2_planning_router.js`: `mountPlanningJourneyContextHeader()`; `public/js/module_journey_context_header.js` pp2 variant | Keep for contextual use (Evidence/Journey) not dominant default shell | superseded pattern list, `PP2-P5-NG-012` | High |
| G0-002-012 | Status strip mounted globally in context host across surfaces | Refactor | `public/js/pp2_planning_router.js`: `mountPlanningStatusBadge()`; `public/js/pp2_planning_status_badge.js` | Reuse badge in list rows and selected summary only | superseded default shell pattern | Medium |
| G0-002-013 | Handoff card component exposed as ordinary primary work content | Hide/Defer + Relocate | `public/js/pp2_planning_handoff_card.js` | Keep component for on-demand Evidence Drawer/Technical Details flows | `PP2-P5-NG-002`, `PP2-P5-NG-005`, `PP2-P5-NG-009` | Medium |
| G0-002-014 | Default package code fallback hardwires WORKS sample package for shell mounts | Refactor | `public/js/pp2_planning_router.js`: `DEFAULT_PP2_PACKAGE_CODE`, `resolveHeaderConfig()` | Drive selection from active queue/list selection state | reset workbench model | Medium |

## 3) Navigation delta (required IA vs current)

Required persistent Planning IA (reset):
1. Planning Home
2. Approved Demands
3. Plans
4. Packages
5. Released to Tender

Current persistent Planning child links from fixture:
- Planning Home
- Approved Demands
- Packages
- Released to Tender
- Planning Evidence

Required changes:
- Remove persistent `Planning Evidence` child link.
- Add `Plans` child link and route.
- Keep all Evidence/Technical/Audit access contextual (button/drawer/explicit action).

## 4) Route delta inventory

| Route contract | Current state | Action |
|---|---|---|
| `/desk/procurement-planning/plans` | Falls back to home | Add explicit plans route support in router/sidebar/registry |
| `/desk/procurement-planning/packages/<package_code>` | Falls back to home | Implement path-style package detail route handling |
| `/desk/procurement-planning/evidence` | Exposed as ordinary submenu route | Remove from persistent IA, re-home evidence access contextually |

## 5) Test impact matrix (rewrite/retire/keep)

| Test file | Current behavior encoded | Decision | Why |
|---|---|---|---|
| `tests/ui/smoke/procurement/procurement-planning-handoff-card-p5-005.spec.ts` | Expects package handoff card stack as default main content | Retire or repurpose | Conflicts with reset package workbench model |
| `tests/ui/smoke/procurement/procurement-planning-primary-shell-p5-002.spec.ts` | Asserts shell/right panel and route behavior tied to superseded defaults | Rewrite | Right panel/stub patterns are superseded |
| `tests/ui/smoke/procurement/procurement-planning-journey-context-p5-003.spec.ts` | Validates dominant default journey header mount | Rewrite | Journey context becomes contextual, not dominant default shell |
| `tests/ui/smoke/procurement/procurement-planning-status-badges-p5-004.spec.ts` | Validates badge placement under journey header context strip | Rewrite (partial keep) | Badge mapping stays; placement contract changes to workbench rows/summary |
| `tests/ui/smoke/procurement/procurement-planning-sidebar-p5-001.spec.ts` | Includes `Planning Evidence` and lacks `Plans` in expected surfaces | Rewrite | Must match reset five-item IA |
| `setup/tests/test_procurement_planning_sidebar_p5_001_contract.py` | Expects fixed five children incl. `Planning Evidence` | Rewrite | Backend contract must match new IA fixture |
| `setup/tests/test_workspace_sidebar_fastpath.py` | Requires evidence fast-path keys | Rewrite | Boot keys should follow reset IA and contextual evidence model |
| `procurement_planning/tests/test_procurement_planning_testids_g2.py` | Reads testids from legacy `procurement_planning_workspace.js` | Rewrite | Canonical testids must bind to active reset renderer, not unloaded legacy file |

## 6) Retain / preserve list (must not be removed in G0-002)

These are preserved and only re-exposed contextually:
- Backend services and records for planning handoff/evidence (`PLANINCL`, `PKGREL`, `PKGCONSUME`) and release/readiness controls.
- Permission/state enforcement at server layer.
- `pp2_planning_status_badge.js` normalization/mapping logic (reuse in workbench rows/summary).
- `pp2_planning_handoff_card.js` business-mode rendering logic (reuse only inside evidence-on-demand context).
- Router shell lifecycle helpers that keep Procurement shell context and stable sidebar mount behavior.

This gate changes default UI exposure, not backend governance rigor.

## 7) Proposed implementation sequence (for downstream gates)

1. P5A: remove persistent Evidence nav + stub/right-panel implementation copy + default handoff-primary packages surface.
2. P5A/P5D: add plans route and update nav/registry/boot mapping to reset IA.
3. P5D/P5E: implement packages workbench and package detail routes; do not default to handoff stacks.
4. P5F/P5G: relocate handoff/evidence/technical disclosure to explicit Evidence Drawer and permission-aware details.
5. Rewrite legacy tests/contracts to match reset selectors and IA.

## 8) Tracker evidence block for G0-002

Implementation Evidence:
- Code path(s):
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/procurement_planning_workspace.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/module_journey_context_header.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_handoff_card.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_status_badge.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json`
  - `apps/kentender_v1/kentender_core/kentender_core/public/js/kt_module_registry.js`
  - `apps/kentender_v1/kentender_core/kentender_core/module_registry.py`
- Component/template path(s): same as above (JS components/router/sidebar fixture)
- Route path(s): `/desk/procurement-planning`, `/approved-demands`, `/plans`, `/packages`, `/packages/<package_code>`, `/releases`, `/evidence` (to be de-persisted)
- API/service path(s), if applicable: backend planning/evidence services retained (no backend removal in this gate)

Test Evidence:
- Test path(s):
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-sidebar-p5-001.spec.ts`
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-primary-shell-p5-002.spec.ts`
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-journey-context-p5-003.spec.ts`
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-status-badges-p5-004.spec.ts`
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-handoff-card-p5-005.spec.ts`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_procurement_planning_sidebar_p5_001_contract.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_workspace_sidebar_fastpath.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/procurement_planning/tests/test_procurement_planning_testids_g2.py`
- Command(s) run: N/A for G0-002 planning gate
- Result: N/A for G0-002 planning gate

Review Notes:
- G0-002 output is explicit and file-mapped.
- No-go IDs are mapped to each superseded pattern.
- Backend governance/handoff controls are explicitly retained.
