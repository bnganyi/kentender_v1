# G0-016 — Label harmonisation (evidence)

## Goal

Ship **G0-016** so Desk copy matches procurement IA (**Strategy Alignment**, **Budget & Funding**) while **routes**, `link_to` targets, `frappe.workspaces` keys (slug of workspace **`name`**), and **`boot_session`** maps keyed by workspace document **`name`** stay stable. **Done** for this ticket: fixtures + JS titles + Procurement Configuration labels + migrate sync + automated tests + trainer glossary (**LV-G0-016-03**).

**Status (tracker):** **Accepted** (**G0-016** + **LV-G0-016-01…03**) — see [implementation tracker §5 / §18.0](./3. procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).

## Implementation summary

| Area | Change |
|------|--------|
| Workspace fixtures | `label` = harmonised; **`title`** = **`name`** (stable route input for Frappe). Paths: `kentender_strategy/.../workspace/strategy_management/strategy_management.json`, `kentender_budget/.../workspace/budget_management/budget_management.json`. |
| Workspace Sidebar (native modules) | `strategy.json`, `budget.json` — display **`label`** only; **`link_to`** unchanged. |
| Desk shells | `strategy_workspace.js`, `budget_workspace.js` — visible `__("Strategy Alignment")` / `__("Budget & Funding")`; identity checks still use **`Strategy Management` / `Budget Management`**. |
| Procurement Configuration | `procurement.json` specialist row labels **(full)**; Python contracts `test_procurement_sidebar_g0_012_contract.py`, `test_procurement_sidebar_g0_014_contract.py`. |
| Migrate | `after_migrate` in `kentender_strategy/install.py` and `kentender_budget/install.py` forces **`label`** after import and resets **`title`** to the stable value (see glossary). |
| Regression | `kentender_strategy/tests/test_g0_016_workspace_route_labels.py` asserts DB **`title`** / **`label`** invariants. |

## Build / migrate / cache (site: `kentender.midas.com`)

```bash
# After `public/js` edits only (already run for this change set when JS touched):
# from bench root:
# ./scripts/bench-with-node.sh build --app kentender_strategy
# ./scripts/bench-with-node.sh build --app kentender_budget

bench --site kentender.midas.com migrate
bench --site kentender.midas.com clear-cache
# bench restart   # on long-lived hosts if bootinfo is sticky in workers
```

## Automated verification (commands + outcome)

Run on **2026-05-15** in this bench:

```bash
bench --site kentender.midas.com run-tests --app kentender_strategy --module kentender_strategy.tests.test_g0_016_workspace_route_labels
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_procurement_sidebar_g0_012_contract
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_procurement_sidebar_g0_014_contract
```

From `apps/kentender_v1`:

```bash
npx playwright test \
  tests/ui/smoke/workspace-discoverability.spec.ts \
  tests/ui/smoke/workspace-desk-clickthrough.spec.ts \
  tests/ui/smoke/budget/budget-landing.spec.ts \
  tests/ui/smoke/procurement/g0-014-configuration-specialist-links.spec.ts \
  --project=chromium
```

**Result:** Python tests **OK**. Playwright (targeted G0-016 batch): **15 passed**, **1 skipped** only when `strategy.manager@moh.test` lacked Budget **Workspace** role (resolved by adding **Strategy Manager** to `Budget Management` workspace `roles`); re-run of `budget-landing.spec.ts:65` passes for that user.

## Related artifact

- [G0-016_label_harmonisation_glossary.md](./G0-016_label_harmonisation_glossary.md) (**LV-G0-016-03**).
