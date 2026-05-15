# G0-015 — Cross-app workspace links (Procurement rail on Strategy/Budget)

**Tracker:** **G0-015**, **LV-G0-015-01**, and **LV-G0-015-02** are **Accepted** in [implementation tracker §5 / §18.0](./3. procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (reviewer sign-off recorded). The combined **G0-010–G0-017** exit is **closed**: **G0-017** + **LV-G0-017-01…03** are **Accepted** (see [G0-017_ia_regression_evidence.md](./G0-017_ia_regression_evidence.md)).

## Goal

Ensure **Strategy Alignment** and **Budget & Funding** (Procurement spine) open **Strategy Management** / **Budget Management** without permission errors, and that the **Procurement** left rail stays mounted (including after hard refresh). Tie desk behaviour to [ADR-PLC-003](./ADR-PLC-003_desktop_procurement_shell_two_layer_ia.md) / **LV-G0-010-01**. **API** cross-app contracts remain **LV-R5-XAPP-01** (out of scope here).

## Audit (workspace `roles` vs Frappe `desktop.Workspace`)

Frappe’s wrapper in `apps/frappe/frappe/desk/desktop.py` (`class Workspace`) enforces:

1. **Module allow-list** — workspace `module` must be in the user’s `allow_modules` unless the user is a Workspace Manager.
2. **`is_permitted()`** — if the `Workspace` DocType child **`roles`** is non-empty, the session user must **share at least one** role (`has_common`); if **`roles` is empty**, access is allowed (subject to module gate).

After **G0-014**, **Strategy Management** listed only specialist roles, so **Requisitioner** (and other spine roles) failed **(2)** and could not load the **Strategy Alignment** wrapper. **G0-015** adds the **minimum general procurement roles** that appear on the **G0-011** spine for those links: **Requisitioner**, **Procurement Planner**, **Procurement Officer**, **Department Approver**, **Auditor** — on **both** Strategy and Budget workspace fixtures (Budget already had specialists; general roles were still missing).

Frappe’s **module gate** in `Workspace.__init__` requires the workspace’s **`module`** string to appear in the user’s `allow_modules` (unless Workspace Manager). Spine roles do **not** share a single business module (e.g. **Requisitioner** gets **Demand Intake** from `Demand`; **Procurement Officer** may lack that but has **Kentender Procurement** / **Procurement Planning**). The **intersection** that still appears for every logged-in Desk user is **`Desk`** (core Frappe module), so **`module` on both wrapper workspaces is `Desk`** while `app` on the Workspace row remains `kentender_strategy` / `kentender_budget`. This satisfies the gate without granting blanket read on Strategy/Budget business masters.

Canonical JSON:

- `apps/kentender_v1/kentender_strategy/kentender_strategy/kentender_strategy/workspace/strategy_management/strategy_management.json`
- `apps/kentender_v1/kentender_budget/kentender_budget/kentender_budget/workspace/budget_management/budget_management.json`
- `apps/kentender_v1/kentender_procurement/kentender_procurement/kentender_procurement/workspace/procurement_home/procurement_home.json` (**module** `Desk` for spine entry / module gate)

**Planning Authority** remains **excluded** from Strategy workspace `roles` per **G0-011** / **G0-014** (PA uses **Budget** specialist paths; **Strategy Alignment** in the spine for PA may still be a product follow-up if PA must not land on Strategy Management).

**Procurement Home** workspace **`module`** is also set to **`Desk`** so spine users without **`Kentender Procurement`** in `allow_modules` (e.g. **Requisitioner**) can load **`/app/procurement-home`** and see the Procurement sidebar (Frappe `Workspace.__init__` gate).

## Boot session / sidebar fast-path (LV-G0-015-01)

| Mechanism | Path |
|-----------|------|
| `boot_session` hook | `apps/kentender_v1/kentender_procurement/kentender_procurement/hooks.py` → `patch_bootinfo` |
| Implementation | `apps/kentender_v1/kentender_procurement/kentender_procurement/setup/workspace_permissions.py` — rebuilds **Procurement** / **Planning** / **Demand Intake** sidebars into `bootinfo.workspace_sidebar_item` and injects **`strategy management`** / **`budget management`** keys mapped to the **Procurement** payload (`_KT_WORKSPACE_TO_SIDEBAR`). |

This matches the **two-layer IA** intent in **ADR-PLC-003**: technical apps remain separate; Desk keeps a **single Procurement shell** rail when viewing Strategy/Budget workspace routes.

## Automated verification

1. **Boot map + requisitioner workspace gate**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_g0_015_cross_app_workspace_boot`

2. **Existing fast-path regression**  
   `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_workspace_sidebar_fastpath`

3. **Playwright (general role)** — from `apps/kentender_v1`:  
   `npx playwright test tests/ui/smoke/procurement/g0-015-cross-app-rail.spec.ts --reporter=line`  
   Logs in as **Requisitioner**, opens **`/app/procurement-home`**, then visits **`/desk/strategy-management`** and **`/desk/budget-management`** and asserts **Procurement Home** remains visible in **`.body-sidebar`** (same workspace targets as **Strategy Alignment** / **Budget & Funding** spine links; spine label clicks depend on `frappe.workspaces` hydration and remain covered by Administrator flows in `procurement-sidebar-g0-012.spec.ts`).

## Migrate / cache

After changing workspace JSON:

```bash
bench --site kentender.midas.com migrate
bench --site kentender.midas.com clear-cache
```

On full bench hosts, **`bench restart`** after migrate when gunicorn workers cache stale boot data.

## Out of scope

- **LV-R5-XAPP-01** (server allowlist for procurement APIs called from Strategy/Budget apps).

Label harmonisation is **G0-016** (see [G0-016_label_harmonisation_evidence.md](./G0-016_label_harmonisation_evidence.md)); it was listed here only while that gate was open.
