# LV-G0-016-03 — Label harmonisation glossary (trainers / internal)

## Goal

Give trainers and support a single place to map **legacy Desk names** to **procurement IA names** (**Strategy Alignment**, **Budget & Funding**) without confusing them with **technical keys** (workspace document `name`, URL slugs, boot maps) that must stay stable for routing and automation.

## Old vs new (user-facing)

| Old label (headline / spine) | New label (user-facing) | Where it appears | Unchanged technical key / route |
|------------------------------|-------------------------|------------------|----------------------------------|
| Strategy Management | Strategy Alignment | Workspace Sidebar (Strategy module), Procurement spine + Configuration **(full)** row labels, `strategy_workspace.js` page title (`data-testid="strategy-page-title"`) | Workspace **`name`**: `Strategy Management`. Desk path continues **`/desk/strategy-management`**. Client guards still compare workspace **`name`** / slug `strategy-management`, not the headline string. |
| Budget Management | Budget & Funding | Workspace Sidebar (Budget module), Procurement spine + Configuration **(full)** row labels, `budget_workspace.js` page title (`data-testid="budget-page-title"`) | Workspace **`name`**: `Budget Management`. Desk path continues **`/desk/budget-management`**. |
| Strategy Management (full) | Strategy Alignment (full) | Procurement `workspace_sidebar/procurement.json` — Configuration specialist link **label** only | **`link_to`** remains `Strategy Management` (workspace name). |
| Budget Management (full) | Budget & Funding (full) | Same | **`link_to`** remains `Budget Management`. |

## Workspace `title` vs `label` (important)

- **`label`** on the `Workspace` document is harmonised (**Strategy Alignment** / **Budget & Funding**) for list/metadata consistency.
- **`title`** on the `Workspace` document stays **Strategy Management** / **Budget Management**. Frappe’s Desk module tile → first workspace navigation passes `workspaces.title` into `frappe.utils.generate_route` for public workspaces (`apps/frappe/frappe/desk/page/desktop/desktop.js` → `utils.js`). If `title` were changed to the harmonised headline, public routes would slugify to broken paths (for example `budget-&-funding`).

## Explicitly unchanged (G0-013 scope)

- **Desktop Icon** labels under Strategy/Budget apps remain **Strategy** / **Budget** (module tiles), per **G0-013** — not part of **LV-G0-016-01/02**.

## Translation note

English `__()` source strings changed for visible shells; if `.po` files are introduced later, reconcile keys then.
