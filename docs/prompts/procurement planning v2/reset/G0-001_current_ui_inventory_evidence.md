# G0-001 Current UI Inventory Evidence

Date: 2026-05-26  
Role used: Administrator  
Site: `kentender.midas.com` via `http://127.0.0.1:8000`

## 1) Route inventory matrix (current UI)

| Route requested | Final URL | Visible default UI blocks | Key testids seen | Source file/function | Reset status |
|---|---|---|---|---|---|
| `/desk/procurement-planning` | `/desk/procurement-planning` | Primary shell + journey header + status strip + canonical stub copy | `pp2-primary-workspace-shell`, `pp2-module-journey-context-header`, `pp2-package-status-strip`, `pp2-canonical-surface` | `pp2_planning_router.js` -> `ensurePrimaryWorkspaceShell()`, `mountPlanningJourneyContextHeader()`, `mountPlanningStatusBadge()`, `renderSurfaceShellStub()` | Non-compliant |
| `/desk/procurement-planning/approved-demands` | `/desk/procurement-planning/approved-demands` | Same shell + context + canonical stub copy (no approved-demands workbench) | `pp2-approved-demands-page`, `pp2-canonical-surface` | `pp2_planning_router.js` -> `readSurfaceSlug()`, `renderSurfaceShellStub()` | Non-compliant |
| `/desk/procurement-planning/plans` | `/desk/procurement-planning` | Redirects/falls back to Planning Home shell/stub | `pp2-planning-home`, `pp2-canonical-surface` | `pp2_planning_router.js` (`readSurfaceSlug()` has no `plans`) | Non-compliant |
| `/desk/procurement-planning/packages` | `/desk/procurement-planning/packages` | Shell + journey header + status strip + **handoff stack (3 cards)** in main host | `pp2-package-workbench`, `pp2-package-handoff-stack`, `pp2-planning-handoff-card` | `pp2_planning_router.js` -> `mountPlanningHandoffStack()`, `buildHandoffCardsFromDetail()` | Non-compliant |
| `/desk/procurement-planning/packages?package_code=PKG-MOH-2026-001` | same | Same as packages route; 3-card handoff stack and status strip | same as above | same as above | Non-compliant |
| `/desk/procurement-planning/releases` | `/desk/procurement-planning/releases` | Shell + context + canonical stub copy (no released workbench) | `pp2-released-to-tender-page`, `pp2-canonical-surface` | `pp2_planning_router.js` -> `renderSurfaceShellStub()` | Non-compliant |
| `/desk/procurement-planning/packages/PKG-MOH-2026-001` | `/desk/procurement-planning` | Path-style package detail route not active; falls back to home shell/stub | `pp2-planning-home`, `pp2-canonical-surface` | `pp2_planning_router.js` + URL sync logic | Non-compliant |

## 2) Current render/code map

| Visible block/pattern | Current owner | Evidence |
|---|---|---|
| Planning shell chrome, sidebar route patching, context host/main host/right panel | `public/js/pp2_planning_router.js` | `ensurePrimaryWorkspaceShell()`, `mount()` |
| Journey context header (compact + technical disclosure) | `public/js/module_journey_context_header.js` | `ModuleJourneyContextHeader.render(..., { variant: \"pp2\" })` from router |
| Status strip badge in context host | `public/js/pp2_planning_status_badge.js` + router | `mountPlanningStatusBadge()` |
| Packages default handoff stack (inclusion/release/consumption) | `public/js/pp2_planning_handoff_card.js` + router | `mountPlanningHandoffStack()` + `buildHandoffCardsFromDetail()` |
| Canonical placeholder/stub copy | router | `renderSurfaceShellStub()` hardcoded copy |
| Legacy workspace renderer (not loaded) still contains handoff-heavy package detail and technical details | `public/js/procurement_planning_workspace.js` | file exists with `pp2-package-handoff-stack`, `pp2-business-summary`, technical details block |

## 3) Asset load / activation inventory

From `hooks.py` current Desk includes:

- Loaded JS: `pp2_planning_router.js`, `module_journey_context_header.js`, `pp2_planning_status_badge.js`, `pp2_planning_handoff_card.js`
- Loaded CSS: `pp2_planning_page.css`, `module_journey_context_header.css`, `pp2_planning_status_badge.css`, `pp2_planning_handoff_card.css`
- Not loaded as active app shell: `procurement_planning_workspace.js` (still present in repo)

## 4) Planning navigation audit vs reset IA

### Required persistent Planning IA (reset)

1. Planning Home  
2. Approved Demands  
3. Plans  
4. Packages  
5. Released to Tender

### Observed Planning submenu labels in live UI

- Planning Home
- Approved Demands
- Packages
- Released to Tender
- Planning Evidence

### Result

- Missing required: **Plans**
- Extra forbidden persistent item: **Planning Evidence**
- IA status: **Non-compliant**

## 5) Reset no-go check (current violations)

Mapped to tracker no-go section in reset tracker:

- **PP2-P5-NG-003**: Planning Evidence appears as persistent ordinary Planning submenu.
- **PP2-P5-NG-002**: Packages shows Planning Inclusion/Release/Consumption card stack as primary content.
- **PP2-P5-NG-007**: Implementation-stage copy visible (`9.1 shell baseline active`, `feature content is intentionally deferred`).
- **PP2-P5-NG-012**: UI behavior still aligned with superseded component-led path rather than reset IA.

Additional route-contract gaps:

- Plans route missing (`/plans` resolves to home).
- Path-style package detail route not active (`/packages/<code>` collapses to home).

## 6) Screenshot index (captured)

- `g0-001-desk-procurement-planning.png`
- `g0-001-desk-procurement-planning-approved-demands.png`
- `g0-001-desk-procurement-planning-plans.png`
- `g0-001-desk-procurement-planning-packages.png`
- `g0-001-desk-procurement-planning-packages-package-code-PKG-MOH-2026-001.png`
- `g0-001-desk-procurement-planning-releases.png`
- `g0-001-desk-procurement-planning-packages-PKG-MOH-2026-001-path.png`

## 7) Top findings summary

1. Current UI is still shell/stub-centric for non-packages surfaces; reset workbench surfaces are not implemented.
2. Packages route currently violates reset by defaulting to handoff stack primary content.
3. Planning navigation violates reset IA (persistent Planning Evidence, missing Plans).
4. Route contract for plans and package-detail path is incomplete.
5. Existing code clearly identifies refactor anchors (`pp2_planning_router.js` and navigation labels) for next gate items (G0-002/G0-003/P5A).

