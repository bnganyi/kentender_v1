# G0-013 — App grid / module tiles (Strategy & Budget de-emphasis)

**Tracker:** G0-013 and LV-G0-013-01…03 are **Accepted** in [implementation tracker §5 / §18.0](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md). **LV-G0-017-01** is advanced to **Accepted** using the same Playwright spec (general-role home grid). The combined **G0-010–G0-017** exit is **closed** on the implementation tracker (**G0-017** + **LV-G0-017-01…03** **Accepted**); see [G0-017_ia_regression_evidence.md](./G0-017_ia_regression_evidence.md).

## Goal

For **general procurement roles**, **Strategy** and **Budget** must not appear as peer **Desk `/app` home** module tiles. **System Manager**, **Administrator**, **Strategy Manager**, and **Budget** specialists (**Planning Authority**, **Finance Reviewer**) retain tiles per **G0-011**. **Procurement** stays the obvious primary tile for general roles (empty `roles` on that Desktop Icon).

## Canonical fixtures (code)

| Area | Path |
|------|------|
| Strategy Desktop Icon (`hidden`, `roles`) | `apps/kentender_v1/kentender_strategy/kentender_strategy/desktop_icon/strategy.json` |
| Budget Desktop Icon (`hidden`, `roles`) | `apps/kentender_v1/kentender_budget/kentender_budget/desktop_icon/budget.json` |
| Procurement Desktop Icon (unchanged; all roles) | `apps/kentender_v1/kentender_procurement/kentender_procurement/desktop_icon/procurement.json` |
| Post-migrate Strategy icon re-import | `apps/kentender_v1/kentender_strategy/kentender_strategy/install.py` → `_sync_strategy_desktop_icon()` |
| Post-migrate Budget icon re-import | `apps/kentender_v1/kentender_budget/kentender_budget/install.py` → `_sync_budget_desktop_icon()` |
| Frappe permission gate | `apps/frappe/frappe/desk/doctype/desktop_icon/desktop_icon.py` — `DesktopIcon.is_permitted` (non-empty `roles` → user must hold one) |

### Role matrix applied (G0-011)

| Desktop Icon | `hidden` | `roles` |
|--------------|----------|---------|
| **Strategy** | `0` | System Manager, Administrator, Strategy Manager (**not** Planning Authority). |
| **Budget** | `0` | System Manager, Administrator, Planning Authority, Finance Reviewer. |

## Automated verification

1. **Desktop Icon rows after migrate (integration)**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_desktop_icon_g0_013`

2. **Playwright (home grid / `a.desktop-icon[data-id=…]`)**  
   From `apps/kentender_v1`:  
   `npx playwright test tests/ui/smoke/procurement/g0-013-app-grid-deemphasis.spec.ts --reporter=line`  
   (Chromium + site per `playwright.config.ts` / `.env.ui`.)  
   Covers: **Requisitioner** and **Procurement Planner** (no Strategy/Budget; Procurement tile visible); **Strategy Manager** (Strategy tile); **Planning Authority** (Budget tile, no Strategy tile). **Finance Reviewer** is covered by fixture roles but not duplicated in Playwright when that seed user is absent on a given site.

## Build / migrate (agent run)

- `bench --site kentender.midas.com migrate` — **OK** (re-imports Strategy/Budget Desktop Icon JSON via app `after_migrate` hooks).
- `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_desktop_icon_g0_013` — **OK** (3 tests).
- `npx playwright test tests/ui/smoke/procurement/g0-013-app-grid-deemphasis.spec.ts --reporter=line` — **OK** (4 tests).
- `bench restart` — skipped in agent WSL when `supervisorctl` is unavailable; run on a full bench host after deploy.

## Notes

- **Procurement tile click** for some general roles can show Frappe’s *“Icon is not correctly configured…”* when `get_route` cannot resolve the first permitted workspace from `frappe.boot.workspace_sidebar_item` (see `apps/frappe/frappe/desk/page/desktop/desktop.js` → `get_route`). That is orthogonal to G0-013 role-gating of Strategy/Budget; LV-G0-013-03 here is satisfied by **tile visibility** on `/app` for Requisitioner.
- Combined exit **G0-010–G0-017** is **closed** on the implementation tracker (**G0-017** **Accepted**).
