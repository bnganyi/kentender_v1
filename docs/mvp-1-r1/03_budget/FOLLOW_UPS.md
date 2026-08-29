# Budget & Funding — outstanding follow-ups

Loose ends left behind by the **BUD-CHG-001 v1.2** rebuild, found from outside
the module and parked here rather than fixed in place, because they belong to
`kentender_budget` (and, for FU-03, `kentender_strategy`) rather than to the
change that tripped over them.

**Found:** 2026-08-29, while running the `kentender_procurement` setup/sidebar
suites during NDS-CHG-001 v1.1 Phase 8.
**Status:** all open. None was introduced by Phase 8 — each was already failing
before it, and none is caused by the Departmental Needs rebuild.

## Why these were not fixed on the spot

`bench migrate` is clean on `kentender.midas.com` today, so nothing here is
visibly broken on this site. FU-01 is the one to look at first anyway: it is
latent rather than harmless, and it fails a **fresh install**, not this one.

## Register

| ID | Item | Severity | Owner |
|---|---|---|---|
| FU-01 | Patch `g013` imports a module deleted by the rebuild — a fresh site install fails | **High** — breaks whole-site migrate on a new site | `kentender_budget` + `kentender_procurement` |
| FU-02 | `Budget Management` Workspace no longer exists; two tests still require it | Medium | `kentender_budget` |
| FU-03 | Requisitioner cannot load the `Strategy Management` Workspace shell | Medium | `kentender_strategy` |
| FU-04 | Retired `budget-builder` / `budget-workbench` routes still referenced in three places | Low | `kentender_procurement` |

---

### FU-01 — `g013` patch imports `kentender_budget.services.budget_workspace`, which is gone

`kentender_procurement/patches/g013_ensure_strategy_budget_workspace_rows.py`
does, at module scope inside `execute()`:

```python
from kentender_budget.services.budget_workspace import ensure_budget_workspace
```

`budget_workspace.py` was deleted by **`ab785c6d`** ("complete service-layer
rewrite for BUD-CHG-001 v1.2 §9"). The patch is still listed in
`kentender_procurement/patches.txt` (post_model_sync).

**Why this site is fine and a new one is not.** `g013` is already recorded in
this site's `Patch Log`, so `bench migrate` skips it — which is exactly why
three clean migrates during Phase 8 said nothing. On a site that has never run
it, the patch executes and raises `ModuleNotFoundError`, failing the **whole
bench migrate**, not just `kentender_budget`. This is the same failure shape
recorded for the sidebar reverse-sync: a dangling cross-app reference inside a
migrate step takes down every app's migrate with it.

**Evidence**

```
$ bench --site kentender.midas.com run-tests --app kentender_procurement \
    --module kentender_procurement.setup.tests.test_g013_ensure_workspace_rows_patch
ERROR test_g013_execute_ensures_cross_app_workspaces
ModuleNotFoundError: No module named 'kentender_budget.services.budget_workspace'
```

**To decide when picking this up:** does BUD-CHG-001 v1.2 still want a
`Budget Management` Workspace at all? The Procurement rail no longer links to
one — its row is now `label: "Budget & Funding", link_to: "budget-funding",
link_type: "Page"`, pointing at the rebuilt Vue-in-Desk Page. If the Workspace
is genuinely retired, the fix is to drop the Budget half of `g013` (and, since
patches do not re-run, add a small superseding patch or leave a comment saying
why the row is gone), not to restore the deleted service.

### FU-02 — the `Budget Management` Workspace does not exist, but tests still require it

Confirmed on `kentender.midas.com`: querying `Workspace` for
`Strategy Management` and `Budget Management` returns **only** Strategy
Management. Two tests still assert the Budget row:

- `setup/tests/test_g013_ensure_workspace_rows_patch.py` — asserts
  `frappe.db.exists("Workspace", "Budget Management")` and that its `public` /
  `is_hidden` / `module` / `app` fields match.
- `setup/tests/test_g0_015_cross_app_workspace_boot.py` —
  `test_patch_bootinfo_maps_strategy_and_budget_to_procurement_rail` requires a
  `budget management` boot fast-path key, and
  `test_requisitioner_can_access_strategy_and_budget_workspace_shells` loops
  over both Workspace names.

Note the same `g013` test also asserts `Strategy Management.app ==
"kentender_strategy"`, and the live row has `app: null` — so that test has a
second, independent failure waiting behind the import error.

Resolve alongside FU-01: whichever way the Workspace question is decided, these
assertions have to follow it.

### FU-03 — requisitioner cannot load the `Strategy Management` Workspace shell

**This one is Strategy, not Budget** — worth stating plainly, because it sits in
a test whose name mentions Budget and it is easy to file in the wrong place.
The test iterates `("Strategy Management", "Budget Management")` and fails on
the **first**, so the Budget half is never reached.

```
$ bench --site kentender.midas.com run-tests --app kentender_procurement \
    --module kentender_procurement.setup.tests.test_g0_015_cross_app_workspace_boot
FAIL test_requisitioner_can_access_strategy_and_budget_workspace_shells
AssertionError: requisitioner@moh.test cannot load Strategy Management (module allow-list?):
```

`frappe.desk.desktop.Workspace.__init__` raises `PermissionError` when the
workspace's module is not in the user's allowed modules. The test's own message
guesses the module allow-list; that guess has not been verified. Two candidates
worth separating before fixing: the requisitioner's module allow-list, or
`Strategy Management.app` being `null` (see FU-02).

### FU-04 — retired `budget-builder` / `budget-workbench` routes still referenced

Neither route exists any more; the rebuilt Page is `budget-funding` (the only
`Page` whose name starts with `budget`). Stale references:

- `setup/tests/test_workspace_sidebar_fastpath.py:170` — asserts a boot
  fast-path key for `budget-builder`. This is the live failure:

  ```
  FAIL test_bootinfo_includes_builder_route_sidebar_keys
  AssertionError: 'budget-builder' not found in {...}
  ```

  The real map comes from `kentender_core.module_registry.get_route_sidebar_keys()`,
  which correctly no longer lists it — so the **test** is asserting the retired
  world, not the code.
- `setup/workspace_permissions.py:138` — `"budget-builder": "Procurement"` in
  the hard-coded dict used only when importing `get_route_sidebar_keys` raises.
  Dead today, but it would silently reintroduce the stale mapping on that
  fallback path. `"form/budget"` on the next line deserves the same check.
- `public/js/procurement_sidebar_header.js:133` — a route regex matching both
  `/desk/budget-workbench` and `/desk/budget-builder`. Dead branch; confirm
  nothing else depends on it before deleting.

---

## Verifying a fix

```bash
cd /home/midasuser/frappe-bench
for m in test_g013_ensure_workspace_rows_patch \
         test_g0_015_cross_app_workspace_boot \
         test_workspace_sidebar_fastpath; do
  bench --site kentender.midas.com run-tests --app kentender_procurement \
    --module kentender_procurement.setup.tests.$m
done
```

All three pass = FU-01 through FU-04 closed. For FU-01 specifically, a passing
test is **not** sufficient evidence: it proves the import resolves, not that a
fresh install migrates. Verify that on a scratch site, or by confirming the
patch no longer runs at all.
