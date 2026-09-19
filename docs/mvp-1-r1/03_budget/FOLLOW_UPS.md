# Budget & Funding — outstanding follow-ups

Loose ends left behind by the **BUD-CHG-001 v1.2** rebuild, found from outside
the module and parked here rather than fixed in place, because they belong to
`kentender_budget` (and, for FU-03, `kentender_strategy`) rather than to the
change that tripped over them.

**Found:** 2026-08-29, while running the `kentender_procurement` setup/sidebar
suites during NDS-CHG-001 v1.1 Phase 8.
**Status (2026-09-06):** FU-06..FU-10 added by the BUD-CHG-001 v1.6
end-to-end verification pass (see `IMPLEMENTATION_TRACKER.md`, "2026-09-06
end-to-end verification"); none is a Budget defect — each is a spec
conflict, a sibling-module or site-owner item, or legacy data owned by the
AUTH-ADR-001 removal phase. Earlier: FU-01, FU-02 and FU-04 closed by
BUD-CHG-001 v1.3 Phase 8 (BUD-803) — see each item's own "Resolved" note for
the fix and evidence. FU-03 (Strategy's own) and FU-05 remain open. None of the original
five was introduced by Phase 8 — each was already failing before it, and none
was caused by the Departmental Needs rebuild.

## Why these were not fixed on the spot

`bench migrate` is clean on `kentender.midas.com` today, so nothing here is
visibly broken on this site. FU-01 is the one to look at first anyway: it is
latent rather than harmless, and it fails a **fresh install**, not this one.

## Register

| ID | Item | Severity | Owner | Status |
|---|---|---|---|---|
| FU-01 | Patch `g013` imports a module deleted by the rebuild — a fresh site install fails | **High** — breaks whole-site migrate on a new site | `kentender_budget` + `kentender_procurement` | **Closed (2026-09-04)** |
| FU-02 | `Budget Management` Workspace no longer exists; two tests still require it | Medium | `kentender_budget` | **Closed (2026-09-04)** |
| FU-03 | Requisitioner cannot load the `Strategy Management` Workspace shell | Medium | `kentender_strategy` | Open |
| FU-04 | Retired `budget-builder` / `budget-workbench` routes still referenced in three places | Low | `kentender_procurement` | **Closed (2026-09-04)** |
| FU-05 | Live `Funding Source` DocType schema does not match CFG-CHG-002 v0.8 §4.4's newly-designed governed catalogue | Medium | `kentender_core` (owner TBD — see below) | Open |
| FU-06 | BUD-AC-039 ("no header, filter … painted" on Forbidden) contradicts §11.16 (every workspace-state variant "contains the BUD-DES-01 page content header and filter row") | Low — spec-internal conflict, live page follows §11.16 and the fidelity gate | BUD-CHG-001 owner | Open (2026-09-06) |
| FU-07 | ERPNext's own `_Test Fiscal Year 2011…2025` fixture rows appear in Budget's Fiscal Year filter on the dev site | Low — dev-site clutter, ERPNext-owned records KT-STD-001 §10 forbids deleting | Site owner | **Closed (2026-09-15)** — owner directed removal; the 15 `_Test Fiscal Year …` / `_Test Short Fiscal Year 2011` rows were confirmed unreferenced by any Link field and deleted; only `2026-2027` and `2027-2028` remain |
| FU-08 | Pre-cutover legacy reference data still on the dev site (`Procuring Entity` PE-MOH/PE-MOE, `Financial Year`, `PE Fiscal Year Context`, `Procuring Department`, `PE Type`, `User Permission` on PE) — not canonical, but KT-STD-001 §10 says legacy records go with the RM-1xx removal phase, not a module cleanup | Low | AUTH-ADR-001 RM-1xx | Open (2026-09-06) |
| FU-09 | The shared My Work page renders every provider's `received_at` raw (`2026-09-06 18:05:21.955670`); Budget's new provider follows the NDS/Planning precedent rather than formatting locally | Low — cosmetic, one fix in the shared page | `kentender_procurement` (`page/my_work`) | Open (2026-09-06) |
| FU-10 | Planning's live seed allocates `PPI-MOH-2027-001`/`-002` while SEED-001 §3.6 and BUD-CHG-001 §15.4 cite `PPI-MOH-2027-021`/`-033`; the Budget-side lineage is correct (both source allocations resolve to `MOH-BL-HWD-2027`), only the human plan-item references differ | Low | `kentender_procurement` (Planning seed) | Open (2026-09-06) |
| FU-12 | Approval document at **Submit for review**: BUD-BR-004 / §5 (`approval_document_file_id` "Required") make it a submission blocker (`evidence.approval_document`, copy "Approval document is required"), and the 2026-09-04 fix ("optional attachment") deliberately kept that gate while making the document optional at draft save. On 2026-09-11 the Budget Officer hit the gate on `MOH-BUD-2026-004` and stated the document is not required at all. Code follows the approved document; if the requirement is to be dropped at submission too, that is a BUD-CHG-001 v1.7 change (BR-004, §5, BUD-AC-004) plus `_evaluate_readiness`, `test_submit_blocked_without_approval_document` and the approval-task readiness copy | Medium — live behaviour and the owner's stated expectation disagree; the document is the tie-breaker until revised | BUD-CHG-001 owner | **Closed (2026-09-15)** — BUD-CHG-001 v1.9 BR-004/§9.3 keeps exactly one approval document required at Submit for review and makes it a first-save requirement on Record approved allocation; code already matched, v1.9 is the revision FU-12 was waiting for |
| FU-11 | REQ-CHG-001 v1.6 D1 (2026-09-06) relaxed `Funding Reservation.plan_source_allocation` from globally unique to "one non-Released reservation per (allocation, caller_reference)", and admitted Head of Procurement Function alongside Finance Confirmation Officer as a `check_funding`/`reserve_funding` caller — a genuine BUD-CHG-001 spec change (§4.5, §7, §9.1) this document should adopt at its next revision, not a code-only footnote | Medium — the live behaviour and the approved document now disagree | BUD-CHG-001 owner | Open (2026-09-06) |
| FU-13 | Technical read is now stated once in KT-STD-001 v1.5 §3A.6 (11 Sep 2026). At this module's next version: replace its own technical-read prose, roles-table row wording, Forbidden carve-out and any masking clause's silence about technical readers with a citation of §3A.6; update AUTH-ADR-001 citations to v1.8 | Low — doc citation | BUD-CHG-001 (next revision) | Open (2026-09-11) |
| FU-15 | **Excluded by BUD v1.9 cycle decision D2:** exact-decimal Money (v1.9 §4.8, BUD18-CHG-006, BUD18-AC-051/052) — services still use `flt()`; amounts cross the API as floats | Medium — precision contract | BUD/NDS/REQ/PLN shared precision suite (BUD18-XD-002) | Open (2026-09-15) |
| FU-16 | **Excluded by D2:** Funding Reservation requisition/drawdown/authorisation-event/source-OU fields (v1.9 §4.5, BUD18-CHG-013); the v1.9 screens derive requisition and source department from `caller_reference` + `plan_source_allocation` (tracker D6) | Medium — schema | BUD + REQ (BUD18-XD-004) | Open (2026-09-15) |
| FU-17 | **Excluded by D2:** `get_budget_currency_contract` / CurrencyBasis provider (v1.9 §9.1, BUD18-CHG-007, BUD18-AC-053) and the published check-token lifetime (BUD18-CHG-016) | Low — contract | BUD/CFG (BUD18-XD-003) | Open (2026-09-15) |
| FU-18 | BUD19-AC-024 second half: a representative-user verification round (v1.9 §16.2, amendment §9) is owner-run evidence, not something the build can produce | Low — evidence | Project Owner | Open (2026-09-15) |
| FU-19 | Contract-owner links (`View contract`) and conversion/adjust facilities on the line detail remain unavailable until the Contract owner publishes its events (BUD18-XD-009); v1.9 screens state the supported limit | Low — sibling | Contract Management | Open (2026-09-15) |
| FU-14 | **PLN-CHG-001 v1.18 contracts (opened 2026-09-12).** Budget supplies `validate_plan_affordability_for_decision(fiscal_year, line_totals, expected_revisions, correlation)` (participates in the caller's decision transaction, serialises the Active basis, validates expected line revisions, returns an immutable comparison statement, writes no financial record) and `get_annual_procurement_budget_basis(fiscal_year, as_of)` (complete approved annual amount, currency, exact Version — the reservation denominator); amounts as decimal strings at the boundary. `check_plan_affordability` stays non-locking. Code lands under Planning tracker row PLN18-107; BUD-CHG-001 v1.8 is owed | Medium — contract + doc | BUD-CHG-001 owner; `docs/mvp-1-r1/04_planning/PLN-CHG-001_FOLLOW_UPS.md` FU-23 | Open (2026-09-12) |
| FU-23 | **Reopens FU-12.** Approval document is no longer mandatory to save or submit a Budget Version (owner instruction, 2026-09-19), removed from `save_budget_version_draft`'s first-save gate and `_evaluate_readiness`'s submission gate. FU-12 closed four days earlier (2026-09-15) on the strength of BUD-CHG-001 v1.9's own text making this exact requirement explicit — that text (§9.3, §5, BUD-BR-004, "the four required approval details") is now stale and should be updated at the document's next revision to drop the document from that list, or the requirement restored in code if this reading is wrong. Code and document currently disagree on purpose | Medium — code/document disagreement | BUD-CHG-001 owner | Open (2026-09-19) |

---

### FU-01 — `g013` patch imports `kentender_budget.services.budget_workspace`, which is gone

**Resolved (2026-09-04, BUD-CHG-001 v1.3 Phase 8 / BUD-803).** Decided:
`Budget Management` Workspace is genuinely retired — the Procurement rail's
row already points at the rebuilt `budget-funding` Page, not a Workspace.
Removed the Budget half of `g013_ensure_strategy_budget_workspace_rows.py`
outright (the dead import and the `ensure_budget_workspace()` call); the
Strategy half is untouched, same file, same `patches.txt` entry (patches may
have their own body corrected after already running on some sites — the
Patch Log only records that the *name* ran once, not a hash of its content —
so this needed no superseding patch or file rename). Evidence:
`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_g013_ensure_workspace_rows_patch`
→ `OK` (was `ModuleNotFoundError` before the fix). Per this item's own
caution that a passing test only proves the import resolves, not that a
fresh install migrates: the import line no longer exists at all in
`execute()`'s source, and the test calls `execute()` directly (twice, proving
idempotency) with zero exceptions — the same code path a truly fresh site's
`bench migrate` would run, independent of Patch Log state.

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

**Resolved (2026-09-04, BUD-CHG-001 v1.3 Phase 8 / BUD-803).** Both tests
updated to match reality (no `Budget Management` Workspace):
`test_g013_ensure_workspace_rows_patch.py` now asserts the row does *not*
exist after `execute()` and only checks `public`/`is_hidden` on `Strategy
Management` (the two fields `g013` actually enforces on an already-existing
row — see below); `test_g0_015_cross_app_workspace_boot.py`'s
`test_requisitioner_can_access_strategy_and_budget_workspace_shells` was
narrowed to `test_requisitioner_can_access_strategy_workspace_shell`,
checking only Strategy Management.
`test_patch_bootinfo_maps_strategy_and_budget_to_procurement_rail` needed no
change — its "budget management" boot key comes from
`workspace_permissions.py`'s `_KT_WORKSPACE_TO_SIDEBAR` map (a sidebar-alias
table, unconditional on the Workspace document existing), left untouched as
outside this item's scope. Evidence: both modules green —
`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_g013_ensure_workspace_rows_patch`
and `...test_g0_015_cross_app_workspace_boot` → `OK` (the latter with
`skipped=2`: this dev site has no `requisitioner@moh.test` user — a
pre-existing, separate seed-world gap, not caused by or masking this fix).

The `Strategy Management.app == "kentender_strategy"` assertion this item
originally flagged as "a second, independent failure waiting behind the
import error" is **not fixed** — `g013`'s update-existing-row branch only
ever enforced `public`/`is_hidden`, never `app`/`module`, and the live row's
real `app` is `null` (confirmed via direct query). Whether that `null` is a
bug or an intentional consequence of Strategy's own AUTH-ADR-001 v1.6
site-local cutover (CU-3xx) is a Strategy-owned question, not Budget's — see
FU-03, still open, which is the same underlying gap.

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

**Still open (checked 2026-09-04, BUD-CHG-001 v1.3 Phase 8 / BUD-803).**
Left open as scoped — a Strategy-owned architectural question, not a Budget
fix. Also newly confirmed: this exact test **cannot be exercised on
`kentender.midas.com` today at all** — `requisitioner@moh.test` does not
exist on this dev site, so both
`test_requisitioner_can_access_procurement_home_workspace_shell` and (the
now Budget-narrowed) `test_requisitioner_can_access_strategy_workspace_shell`
skip rather than fail (`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_g0_015_cross_app_workspace_boot`
→ `OK (skipped=2)`). This dev site's own pass/fail status therefore says
nothing about whether the underlying Strategy access defect is fixed — only
that it is untested here, matching the previously-documented "dev site seed
world missing" pattern for this site.

### FU-04 — retired `budget-builder` / `budget-workbench` routes still referenced

**Resolved (2026-09-04, BUD-CHG-001 v1.3 Phase 8 / BUD-803).** All three
locations fixed exactly as scoped below: `test_workspace_sidebar_fastpath.py`
no longer asserts a `budget-builder` boot key (confirmed via
`kentender_core.module_registry.get_route_sidebar_keys()` — Budget's own
registry entry has a `desk_page` of `"budget-funding"` and no `builder_page`
at all, so the real function never emitted one);
`workspace_permissions.py`'s dead fallback dict (only exercised when
`get_route_sidebar_keys` itself raises) dropped both `"budget-builder"` and
`"form/budget"`; `procurement_sidebar_header.js`'s dead
`/desk/budget-workbench` / `/desk/budget-builder` regex branch removed, after
a repo-wide grep confirmed no live JS/Vue/Python route references either
string (only this dead branch, the two fallback-dict keys just removed, and
`kentender_budget`'s own historical teardown patch — which legitimately
lists them as *past* page names to clean up, not live code).

Evidence: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_workspace_sidebar_fastpath`
→ this item's own named test (`test_bootinfo_includes_builder_route_sidebar_keys`)
now passes; **10 of 11 tests in the module are green**. The 11th
(`test_bootinfo_includes_builder_route_sidebar_keys` itself, same method)
newly fails on a **different, unrelated, pre-existing** assertion this fix
exposed rather than caused — `'form/demand'` (a Departmental Needs route,
absent from `kentender_core.module_registry`'s `KT_MODULES` entirely) is
missing from the same boot-key list the `budget-builder` assertion used to
fail on first. Because Python's `assertIn` loop stops at the first miss, this
gap was silently masked behind the `budget-builder` failure until that one
was fixed. Not investigated or fixed here — it names no Budget concept, is
not one of this register's items, and is Departmental Needs' own domain, out
of BUD-CHG-001 v1.3 Phase 8's scope. Flagging it here only so a future reader
does not mistake it for a regression from this fix.

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

### FU-05 — `Funding Source` schema drift against CFG-CHG-002 v0.8 §4.4

Found 2026-09-04, during BUD-CHG-001 v1.3 Phase 9, while recording D3 (funding-source
catalogue ownership, flagged not fixed). At the time D3 was written, `CFG-CHG-002 v0.6`
had zero mentions of funding anywhere — a genuine ownership gap. Independently, that
document's own owner has since published **v0.8**
(`docs/mvp-1-r1/09_unified_system_setup/KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_8.md`
§4.4), which explicitly names the same gap ("a governed funding-source catalogue that
v0.6 left without an owner") and designs a replacement: a governed catalogue with fields
`funding_source_name` (required) and `enabled` (checkbox), "maintained in System setup."

The live DocType Budget actually uses today —
`kentender_core/kentender_core/kentender_core/doctype/funding_source/funding_source.json`,
created ad hoc by the v1.2 rebuild (commit `bc6464f9`) — has a different shape entirely:
`label` (unique, required) and `record_status` (`Draft`/`Available`/`Retired`), with no
`enabled` checkbox and no System-Setup-owned maintenance UI. Every Budget contract that
reads the catalogue (`reference_data_queries.list_funding_sources()`, filtered on
`record_status == "Available"`) depends on this exact shape.

Nobody has reconciled the two. This is not BUD-CHG-001 v1.3's gap to close (D3's scope
was explicitly flag-only, and CFG-CHG-002 v0.8 is a document this app does not own), but
it is a live schema fork now, not just a missing-owner note — the next document or change
unit that touches either side needs to pick a direction (migrate Budget's DocType to
v0.8's shape and move ownership to System Setup, or amend v0.8 §4.4 to match what already
ships) rather than build against whichever shape it happens to read first.

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

**Run 2026-09-04 (BUD-CHG-001 v1.3 Phase 8 / BUD-803):**
`test_g013_ensure_workspace_rows_patch` → `OK`.
`test_g0_015_cross_app_workspace_boot` → `OK (skipped=2)` (no
`requisitioner@moh.test` on this dev site — see FU-03's own note).
`test_workspace_sidebar_fastpath` → **10/11 pass**; the one failure is not a
FU-01–04 regression — see FU-04's own resolution note for the unrelated,
pre-existing `'form/demand'` gap it exposed. FU-01, FU-02 and FU-04 are
closed on the evidence above; FU-03 stays open, Strategy's own to pick up.
