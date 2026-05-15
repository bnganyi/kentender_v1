# G0-014 — Specialist Strategy / Budget surfaces (evidence)

**Tracker:** G0-014 and LV-G0-014-01…03 are **Accepted** in [implementation tracker §5 / §18.0](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md). **LV-G0-017-03** is **Accepted** via Playwright in this deliverable. The combined **G0-010–G0-017** exit is **closed** on the implementation tracker (**G0-017** + **LV-G0-017-01…03** **Accepted**); see [G0-017_ia_regression_evidence.md](./G0-017_ia_regression_evidence.md).

## Goal

Document and implement how **admin and specialist roles** reach **full Strategy Management** and **full Budget Management** after **G0-013** removed peer home tiles for general roles. **Configuration** must not show specialist-only deep links to general procurement roles. **LV-G0-011-03** (full forbidden-surface matrix automation) remains out of scope; **LV-G0-014-03** is satisfied by **repo JSON** (`display_depends_on`), **Python contract tests**, and **Playwright** for **Administrator** (Configuration + STD Library + both specialist links).

## Matrix alignment (workspace `roles`)

| Workspace | Change vs pre-G0-014 | Rationale ([G0-011](G0-011_role_matrix_shell_visibility.md)) |
|-----------|---------------------|--------------------------------------------------------------|
| **Strategy Management** | Removed **Planning Authority**; added **Administrator**. | Specialist Strategy for PA is **`—`**; desktop tile roles (G0-013) match System Manager, Administrator, Strategy Manager. |
| **Budget Management** | Removed **Strategy Manager**; added **Administrator**, **Finance Reviewer**. | Specialist Budget for Strategy Manager is **`—`** unless dual-role; PA and Finance Reviewer need full Budget per matrix. |

Canonical fixtures (repo paths):

| Workspace | Path |
|-----------|------|
| Strategy Management | `apps/kentender_v1/kentender_strategy/kentender_strategy/kentender_strategy/workspace/strategy_management/strategy_management.json` |
| Budget Management | `apps/kentender_v1/kentender_budget/kentender_budget/kentender_budget/workspace/budget_management/budget_management.json` |

**Migrate:** `apps/kentender_v1/kentender_strategy/kentender_strategy/install.py` imports Strategy workspace with **`force=True`**. `apps/kentender_v1/kentender_budget/kentender_budget/install.py` → `_sync_budget_management_workspace()` includes the inner **`kentender_budget`** package segment so the workspace JSON above is imported (see §Technical note).

## Specialist entry paths (URLs)

| Path | Typical URL | Roles / notes |
|------|-------------|----------------|
| **Desk /app slug** | `/app/strategy-management`, `/app/budget-management` | Same slug rules as `apps/kentender_v1/tests/ui/helpers/routes.ts` (`workspaceAppPath`). |
| **Desk /desk slug** | `/desk/strategy-management`, `/desk/budget-management` | Alternate resolution depending on build; smoke tests accept both. |
| **Procurement spine (wrappers)** | **Strategy Alignment** → Strategy Management; **Budget & Funding** → Budget Management | `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json` (G0-012). |
| **Configuration (G0-014)** | **Strategy Management (full)** / **Budget Management (full)** | Same workspace targets; visibility via `display_depends_on` (mirrors G0-013 desktop icon role sets). |
| **Home module tiles** | `/app` → Strategy / Budget tiles | [G0-013_app_grid_deemphasis_evidence.md](./G0-013_app_grid_deemphasis_evidence.md) — role-gated `Desktop Icon`. |

Cross-app boot / rail consistency is **G0-015**; this doc records current behaviour only.

## Configuration gated links (LV-G0-014-03)

File: `apps/kentender_v1/kentender_procurement/kentender_procurement/workspace_sidebar/procurement.json`

| Label | `link_to` | `display_depends_on` (eval in Desk) |
|-------|-----------|-------------------------------------|
| Strategy Management (full) | Strategy Management | `frappe.user.has_role(['System Manager', 'Administrator', 'Strategy Manager'])` |
| Budget Management (full) | Budget Management | `frappe.user.has_role(['System Manager', 'Administrator', 'Planning Authority', 'Finance Reviewer'])` |

Frappe evaluates these in [sidebar.js](apps/frappe/frappe/public/js/frappe/ui/sidebar/sidebar.js) via `frappe.utils.eval`.

Re-sync after export changes: `kentender_procurement.setup.after_migrate_navigation.reconcile_procurement_navigation_from_exports` (runs from **`after_migrate`** hook).

## Automated verification

1. **G0-012 label order (includes new Configuration rows)**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_procurement_sidebar_g0_012_contract`

2. **G0-014 export contract**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_procurement_sidebar_g0_014_contract`

3. **Playwright (LV-G0-017-03 + 014-03)** — from `apps/kentender_v1`:  
   `npx playwright test tests/ui/smoke/procurement/g0-014-configuration-specialist-links.spec.ts --reporter=line`  
   Covers: **Administrator** — separate flows for **Strategy Management (full)** and **Budget Management (full)** (avoids toggling Configuration closed); **Official STD Library** remains visible with specialist links. Asymmetric **non-admin** gates (e.g. Planning Authority vs Strategy (full)) are enforced by `display_depends_on` in repo JSON (`test_procurement_sidebar_g0_014_contract`); full role-matrix UI negatives remain **LV-G0-011-03**.

## Technical note (budget workspace import path)

`frappe.get_app_path('kentender_budget')` resolves to `…/kentender_budget/kentender_budget`. Canonical **Budget Management** workspace JSON lives under an additional **`kentender_budget`** directory. **`install._sync_budget_management_workspace`** joins that inner segment so **`bench migrate`** applies workspace `roles` updates.

## Manual evidence (optional)

Screenshots: Administrator with **Configuration** expanded showing **Strategy Management (full)** + **Budget Management (full)**; Procurement Planner with **Configuration** expanded showing neither link.
