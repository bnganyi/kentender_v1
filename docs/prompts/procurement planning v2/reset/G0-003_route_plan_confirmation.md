# G0-003 Route Plan Confirmation

Date: 2026-05-26  
Source inputs: `G0-001_current_ui_inventory_evidence.md`, `G0-002_delete_refactor_list.md`

## 1) Canonical reset route contract

Persistent Planning routes (required):

| Screen | Canonical route | Required page selector | Notes |
|---|---|---|---|
| Planning Home | `/desk/procurement-planning` | `pp2-planning-home` | Root Planning surface |
| Approved Demands | `/desk/procurement-planning/approved-demands` | `pp2-approved-demands-page` | Queue/list surface |
| Plans | `/desk/procurement-planning/plans` | `pp2-plans-page` | Required persistent IA item |
| Packages | `/desk/procurement-planning/packages` | `pp2-packages-page` | Primary package workbench |
| Package Detail | `/desk/procurement-planning/packages/<package_code>` | `pp2-package-detail` | Contextual detail route |
| Released to Tender | `/desk/procurement-planning/releases` | `pp2-released-to-tender-page` | Follow-up list |

Contextual only (not persistent submenu):
- Evidence access (drawer/action), not ordinary persistent `/evidence` Planning route.

## 2) Actual repository route mapping (current state)

| Canonical route | Current runtime behavior | Current selector seen | Compliant | Primary owner files |
|---|---|---|---|---|
| `/desk/procurement-planning` | Renders shell + context + status strip + stub content | `pp2-planning-home`, `pp2-canonical-surface` | No | `public/js/pp2_planning_router.js` |
| `/desk/procurement-planning/approved-demands` | Renders shell + stub (no Approved Demands workbench yet) | `pp2-approved-demands-page`, `pp2-canonical-surface` | No | `public/js/pp2_planning_router.js` |
| `/desk/procurement-planning/plans` | Falls back to home via slug fallback and URL sync | `pp2-planning-home` | No | `public/js/pp2_planning_router.js` |
| `/desk/procurement-planning/packages` | Renders handoff card stack as primary content | `pp2-package-workbench`, `pp2-package-handoff-stack` | No | `public/js/pp2_planning_router.js`, `public/js/pp2_planning_handoff_card.js` |
| `/desk/procurement-planning/packages/<package_code>` | Falls back to home (path-style detail not parsed) | `pp2-planning-home` | No | `public/js/pp2_planning_router.js` |
| `/desk/procurement-planning/releases` | Renders shell + stub (no release workbench yet) | `pp2-released-to-tender-page`, `pp2-canonical-surface` | No | `public/js/pp2_planning_router.js` |
| `/desk/procurement-planning/evidence` (superseded) | Still treated as ordinary Planning surface and submenu item | `pp2-planning-evidence-index` | No | `public/js/pp2_planning_router.js`, `workspace_sidebar/procurement.json`, module registries |

## 3) Route ownership map by layer

| Layer | File | Current role |
|---|---|---|
| Runtime route parsing + mount | `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js` | Slug detection, URL normalization, surface mount |
| Sidebar child URL declarations | `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json` | Planning submenu route URLs |
| JS route-prefix registry | `apps/kentender_v1/kentender_core/kentender_core/public/js/kt_module_registry.js` | Route prefixes for module context |
| Python route-prefix registry | `apps/kentender_v1/kentender_core/kentender_core/module_registry.py` | Server-side registry mirror |
| Sidebar fast-path key mapping | `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py` | Boot key-to-sidebar mapping for route visibility |

## 4) Explicit route gaps blocking reset compliance

| Gap ID | Gap | Impacted rows | Owner files |
|---|---|---|---|
| G0-003-G1 | `/plans` route not implemented as dedicated Planning surface | P5A-003, P5D-001 | `pp2_planning_router.js`, `procurement.json`, registries, fast-path mapping |
| G0-003-G2 | Path-style package detail route `/packages/<package_code>` not implemented | P5D-013, P5E-001 | `pp2_planning_router.js` (+ route/selector tests) |
| G0-003-G3 | Persistent ordinary Planning Evidence route/menu still present | P5A-004, no-go `PP2-P5-NG-003` | `procurement.json`, `pp2_planning_router.js`, registries, fast-path mapping |
| G0-003-G4 | Packages route selector/behavior reflects superseded handoff-primary model (`pp2-package-workbench`) | P5D-006, P5D-012 | `pp2_planning_router.js`, handoff card mounting paths |
| G0-003-G5 | Current route handling normalizes unknown slugs to root, hiding route contract failures | P5A-006 redirect strategy | `pp2_planning_router.js` (`readSurfaceSlug`, `syncSurfaceUrl`) |

## 5) Redirect and normalization notes (for downstream implementation)

- Current behavior silently normalizes unknown planning paths to `/desk/procurement-planning`; this masks missing route implementations.
- Downstream P5A-006 route handling should replace fallback collapse with explicit route-specific handling:
  - valid route render
  - safe redirect to canonical destination
  - permission-aware not-found behavior
- Superseded persistent `/evidence` route must be de-persisted from ordinary Planning IA and replaced by contextual Evidence access.

## 6) Downstream dependency map (P5A / P5D / P5E)

| Tracker row | Depends on this route-plan confirmation |
|---|---|
| P5A-003 | Exact five Planning child links contract (includes Plans, excludes Evidence) |
| P5A-004 | Evidence removed as persistent ordinary Planning submenu |
| P5A-006 | Redirect behavior for old/superseded planning routes |
| P5D-001 | Plans route implementation (`/plans`) |
| P5D-006 | Packages route implementation aligned to reset workbench contract |
| P5D-013 | Open Package action must resolve to package detail route |
| P5E-001 | Path-style package detail route implementation |

## 7) Test/contract impact notes for route migration

These tests currently encode pre-reset route assumptions and must be updated during P5A/P5D/P5E execution:

- `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-sidebar-p5-001.spec.ts`
- `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_procurement_planning_sidebar_p5_001_contract.py`
- `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_workspace_sidebar_fastpath.py`

## 8) G0-003 tracker evidence block

Implementation Evidence:
- Code path(s):
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/public/js/pp2_planning_router.js`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json`
  - `apps/kentender_v1/kentender_core/kentender_core/public/js/kt_module_registry.js`
  - `apps/kentender_v1/kentender_core/kentender_core/module_registry.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py`
- Component/template path(s): Router and sidebar/module registry mappings listed above.
- Route path(s):
  - Canonical: `/desk/procurement-planning`, `/approved-demands`, `/plans`, `/packages`, `/packages/<package_code>`, `/releases`
  - Superseded ordinary route to de-persist: `/desk/procurement-planning/evidence`
- API/service path(s), if applicable: N/A for this planning gate.

Test Evidence:
- Test path(s):
  - `apps/kentender_v1/tests/ui/smoke/procurement/procurement-planning-sidebar-p5-001.spec.ts`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_procurement_planning_sidebar_p5_001_contract.py`
  - `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/tests/test_workspace_sidebar_fastpath.py`
- Command(s) run: N/A for G0-003 documentation gate.
- Result: N/A for G0-003 documentation gate.

Review Notes:
- Route table now explicitly maps canonical reset routes to current repository behavior and ownership.
- Non-compliant route gaps are enumerated with downstream tracker linkage.
