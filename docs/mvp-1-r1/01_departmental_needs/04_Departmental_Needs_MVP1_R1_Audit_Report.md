# Departmental Needs MVP-1 R1 — Independent Audit Report

**Audit date:** 19 August 2026
**Scope:** `NDS-CHG-001 v0.2` (approved 18 August 2026) against the actual state of the codebase, one day after the implementation tracker's last entry.
**Method:** Direct code inspection plus execution of the test suites the tracker cites as evidence (not a re-read of the tracker's self-report). Four independent passes: (1) legacy Demands retirement inventory, (2) acceptance-criteria compliance verification, (3) test-evidence re-verification, (4) Planning/Budget/Strategy wiring trace.

## Executive summary

The Departmental Needs module is real, well-built server-side code — schema, lifecycle, authorization, audit trail, idempotency and the allocation projection are all implemented largely as specified, with good test coverage for what they cover. But the tracker's "Partial" self-rating understates two things that change the risk picture:

1. **The canonical page is currently broken in a browser.** `/desk/departmental-needs` calls `get_workspace`, which is not whitelisted for HTTP access. A Playwright run from *this same day* (19 Aug) failed with `Method Not Allowed`. The tracker's "Live page ... pass" claim rests on a Python unit test that calls the function directly, bypassing the whitelist layer that the real page depends on.
2. **The new Planning contract (`PlanNeedAllocation`) has zero UI callers anywhere in the repository.** The live Planning UI — the only way a user can add a line item to a plan today — exclusively drives the *old* `Demand` → `Plan Demand Allocation` path. Retiring the legacy Demand code today would break plan creation, editing, finance confirmation, approval and removal, because nothing has been re-implemented to reach the new contract from the UI.

So the honest state is not "new module mostly done, old module needs cleanup." It is: **the new module is a well-tested backend with a broken front door, sitting next to an old module that is still the only thing actually running in production traffic** — and that old module isn't just present on disk, it is actively re-provisioned by patches on every migrate.

## 1. Legacy Demands module: not dead code, actively re-provisioned

`docs/.../KenTender_NDS-CHG-001...md` §10 forbids reuse, extension, migration, compatibility adapters, redirects, dual reads, feature flags or fallback queries tied to the old Demands implementation. What's actually in the repo violates this on every axis:

| Mechanism | File | Effect |
|---|---|---|
| Patch (`post_model_sync`) | `kentender_procurement/patches/ensure_demands_doctypes.py` | Force re-imports 7 legacy DocType JSONs on **every** `bench migrate` |
| Patch (`post_model_sync`) | `kentender_procurement/patches/ensure_demands_roles.py` | Re-creates 7 legacy Roles on every migrate |
| Patch (`pre_model_sync`) | `kentender_procurement/patches/ensure_demands_module_def.py` | Re-creates Module Def "Demands" on every migrate |
| Module registry | `kentender_procurement/modules.txt` | Lists `Demands` and `Departmental Needs` as co-equal live modules |
| hooks.py assets | `hooks.py:72-105,257-261` | Loads 6 legacy CSS files, ~9 legacy JS files, and 5 legacy page routes (`demands-workspace`, `demand-form`, `demand-review`, `demand-detail`, `demand-performance`) |
| Feature-flag module | `procurement_lifecycle/demand_module_gate.py`, `demands/__init__.py::CONSUMERS_LIVE = True` | Explicit compatibility gate, imported by 11+ files across procurement/budget/strategy |
| Compatibility shim | `procurement_lifecycle/legacy_demand_seed_shim.py` | Literally named and documented as a "compatibility shim" |
| Live dashboard | `procurement_home/services/home_pipeline.py`, `home_actions.py` | Procurement Home's landing-page widgets and action items link to `/desk/demands-workspace`, `/desk/demand-form/{name}`, `/desk/demand-review/{name}` — the legacy module is reachable from the **main landing page**, not just a stale sidebar entry |

Cross-app consumers that still read `Demand`-shaped data directly (not gated, not migrated):

- **Budget** — `services/budget_check_reserve_contracts.py` (`_demand_context()`, `demand_doctype_available()` fallback pattern) sits inside the live `check_funding()`/`reserve_funding()` path; `api/dia_budget_control.py` is self-described as "adapters/shims over MVP-1 contracts" and builds idempotency keys from `Demand` codes; `public/js/budget_live_bind.js` renders `demand_code` throughout the desk UI, including the Check-&-Reserve dialog.
- **Strategy** — `services/strategy_performance.py` and `strategy_contracts.py` read `Demand`, `Demand Strategy Reference`, `Demand Value Treatment` directly for dashboard/funding-headroom calculations, gated by the same `demand_doctype_available()` pattern.
- **Tests** — ~35 Python test files under `demands/tests/`, plus 14 Playwright specs under `tests/ui/smoke/demands/`, plus `tests/ui/smoke/planning/planning-add-demand.spec.ts`, all collected and run by default (no exclusion anywhere in the repo). One file, `test_demands_mvp1_legacy_absence.py`, is misleadingly named — it does not assert the module is absent; it imports and exercises it, and only checks for the *absence of specific dual-write markers* within an otherwise fully-live module.

**Precedent exists for how to do this cleanly**: `docs/STD_MODULE_POC_RETIRED.md` documents a prior retirement (STD Config/Library POC, July 2026) — archive the tree under `archive/`, tag pre-archive, swap routes for a retired-placeholder page, strip hooks.py entries, replace re-provisioning patches with a one-time teardown patch. The pattern for the *predecessor* of this same module (`mvp1_teardown_retire_demand_intake_pre_sync.py`, retiring "Demand Intake") already exists in this same `patches.txt` — it just wasn't applied to the current Demands module.

## 2. Acceptance criteria — independent verdicts (NDS-AC-001..019)

Verified against actual code, not the tracker's self-report.

| ID | Verdict | Basis |
|---|---|---|
| AC-001 | Partial | Page/route exist and are tested, but legacy `/demands`-family routes remain registered (hooks.py), so Departmental Needs is not "the only" route in practice. Route is `/desk/departmental-needs`, not the ledger's literal `/departmental-needs`. |
| AC-002 | Partial | Server-side PE/OU + capability check implemented (`services/permissions.py`); no Need-specific cross-PE/cross-OU negative test exists. |
| AC-003 | Implemented | `NDS_INTAKE_WINDOW_NOT_CONFIGURED` fail-closed, exact code found in `services/context.py:13`. Test coverage is conditional (only runs if a future FY happens to be enabled), not guaranteed. |
| AC-004 | Implemented | Explicit test asserts no procurement-method/category/BOQ/requisition fields on the schema. |
| AC-005 | Partial | Reviewer capability correctly gated to Head of User Department. "Departmental Review Delegate" role is registered but has **no seeded persona, profile, or test** — unexercised. |
| AC-006 | Implemented | "Accepted for planning" used verbatim throughout; no "Approved" label anywhere. |
| AC-007 | Partial | No funding/reservation field or side effect exists in the accept path (implemented by omission); no explicit positive-absence test. |
| AC-008 | Partial | Budget Officer only ever granted read-only capability; no command function accepts it. No negative test proving a write attempt is rejected. |
| AC-009 | Implemented | Planner read-only enforcement is real and tested at both workspace-filter and doctype level. |
| AC-010 | Partial | Audited support-view mechanism exists and is shared with Core, **but the Core test backing it (`test_authorization_gate04`) currently fails** — see §3. No NDS-specific audit assertion exists. |
| AC-011 | Implemented | Need lifecycle state and Plan allocation usage are genuinely separate projections; test proves both values simultaneously. |
| AC-012 | Implemented | Triple-checked server-side (selector filter, doctype validate, allocation service) that only Accepted Needs are eligible. |
| AC-013 | Implemented | Test proves Draft allocation leaves usage at "Not included." |
| AC-014 | Implemented | Test proves Need + Need-line lineage preserved on every allocation. |
| AC-015 | Partial | No code path references Requisition/Tender (true by omission); no structural absence test. |
| AC-016 | **Not implemented** | Legacy Demand schema/services/roles/patches/tests are all still present and actively re-provisioned — see §1. |
| AC-017 | **Not implemented** | The live Planning UI still exclusively calls the legacy `list_eligible_demands`/`add_demand_to_plan` endpoints — an active dual-path, not a dormant leftover. See §4. |
| AC-018 | **Not implemented as claimed** | The NDS seed function (`upsert_departmental_needs`) is only ever called from test `setUpClass` methods. The actual fresh-environment seed orchestrator (`kentender_core/.../orchestrator.py::run_kentender_mvp_v1`) still calls legacy `upsert_demands()` and has **no reference to the new seed function at all**. A genuinely fresh environment would not get the NDS fixture without a developer manually invoking it. |
| AC-019 | Partial | Fail-closed context-scope mechanism exists (`NDS_CONTEXT_OUTSIDE_ASSIGNMENT`); no Departmental-Needs-specific cross-PE/cross-department test exists, only generic Core gates are cited. |

**Tally: 8 Implemented, 9 Partial, 2 Not implemented** — against a tracker that reports 0 explicit "Not implemented" and rates the two failing items ("In progress").

## 3. Test evidence — what the tracker's numbers actually reduce to

| Tracker claim | Result of independently re-running it |
|---|---|
| Departmental Needs schema/lifecycle/authorization — 5/5 pass | **Confirmed.** But composition is mostly happy-path: one schema check, one exact-fixture check, one full happy-path lifecycle walk, one idempotency+fail-closed check, one Planner-view check. No forbidden-transition, downstream-clearance, stale-token, or concurrency matrix exists yet. |
| Departmental Needs UI contract — 1/1 pass | **Confirmed, but weak.** The single test reads JS/CSS files as text and asserts substrings are present. It never loads a DOM or browser — "UI contract" here means static string presence. |
| Plan Need Allocation — 1/1 pass, lineage + over-allocation rejection | **Confirmed and accurately described.** |
| Shared Core authorization gates G01-G04 — 27/27 pass | **Contradicted.** Gates 01-03 pass (7/7 each). Gate 04 is **5/6, one failure**, reproduced twice: `test_diagnostic_is_read_only_and_support_projection_is_explicit_and_audited` expects `authorize_support_record_view(user="Administrator", ...)` to raise `PermissionError` — it doesn't. Actual total is **26/27**. This is the same mechanism AC-010 depends on. |
| Planning Plan-approval gate G05 — 5/5 pass | **Confirmed.** |
| Procurement asset compilation — JS/CSS pass, wrapper fails with `OSError: Errno 95` | **Partially contradicted.** Two independent `bench build` runs (app-scoped and full) both completed cleanly with exit 0 — the described translation-multiprocessing failure did not reproduce here. Likely environment-specific (sandbox syscall restriction); can't be ruled in or out generally. |
| *(not claimed by tracker)* Playwright live-workspace test | **New finding.** `tests/ui/smoke/departmental_needs/departmental-needs-workspace.spec.ts` has 5 tests; only 1 was actually executed in the most recent run (same day, 19 Aug), and it **failed on both attempt and retry**: `Method Not Allowed — Function kentender_procurement.departmental_needs.services.workspace.get_workspace is not whitelisted.` The other 4 tests (viewport/keyboard/a11y) have no run artifacts at all. |

The `get_workspace` whitelist failure is the most important single finding in this audit: it means the canonical `/desk/departmental-needs` page — the thing NDS-G03 and NDS-UI-001 both mark "Live page ... pass" — does not actually render for a real user today. The gap exists because the passing evidence (`test_exact_workspace_fixture_and_separate_usage`) calls the Python function directly, bypassing the HTTP whitelist boundary that the real page depends on (`public/js/departmental_needs_page.js` calls it via `frappe.call`, which does enforce whitelisting).

## 4. Planning wiring: the new contract is inert

Traced every UI→API call site in the Planning module (`public/js/planning_*.js`, resolved through the shared `planning_client_utils.js` wrapper to `kentender_procurement.procurement_planning.api.*`):

- The only line-item entry point, the Add-Demand dialog (`planning_demand_dialog.js`), calls `list_eligible_demands` / `add_demand_to_plan` — both query and write `Demand`/`Demand Item`/`Plan Demand Allocation` directly.
- `list_eligible_needs` / `allocate_need_lines` (the new contract, backed by `services/need_allocations.py`) exist and are correctly implemented server-side, but a repo-wide search for their names in any `.js` file returns **zero matches**. They are called only from the unit test.
- Plan approval (`approve_plan_version.py`) and plan-item removal (`remove_plan_item.py`) do call both `activate_need_allocations`/`reverse_need_allocations` *and* the legacy `Plan Demand Allocation` handling — but since nothing in the UI ever creates a `Plan Need Allocation` row, the new-contract branches always run against an empty set in practice.
- The Plan Item Editor (`get_plan_item_editor.py`) and finance-confirmation drawer (`plan_item_finance.py`) — where Budget's `check_funding`/`reserve_funding` actually get called — contain **zero references to `Plan Need Allocation`**. If a Need-sourced plan item were ever created via the (currently unreachable) new contract, there is no code path to edit it or confirm its funding.
- **Budget has no consumer at all for the new contract**: a repo-wide search in `kentender_budget/` for "Departmental Need" or "Plan Need Allocation" returns zero files. This is a functional gap, not just cleanup debt — even after the UI is wired, funding confirmation for Need-sourced items has nowhere to go.
- **Deleting the legacy Demand doctypes today would break the live UI immediately** — none of the reachable Planning code paths guard `Demand` access with an existence check the way Strategy's `demand_doctype_available()` gate does. Add-Demand dialog, Item Editor, finance drawer, plan approval, and plan-item removal would all break.

## 5. Consolidated answer: reuse, retire, or re-implement?

Direct answer to "check if we need to re-implement":

**Yes — the sequencing in the tracker/ledger is backwards from what's actually safe to execute.** The ledger (§10) says to build Departmental Needs fresh and then retire Demands. What's actually happened is the fresh build was done at the schema/service layer, but the UI and Budget layers were never re-pointed at it — so retiring Demand code now, as NDS-G05 nominally wants next, would break production. The old code cannot simply be "reused" (the ledger forbids it, and it's specifically what's being replaced), but it also cannot be deleted yet, because nothing has replaced its UI and Budget wiring. Concretely, before any legacy retirement work:

1. **Re-implement the Planning UI's add/select flow** against `list_eligible_needs`/`allocate_need_lines` instead of `list_eligible_demands`/`add_demand_to_plan`. This is new UI work, not a port — the current dialog is `Demand`-shaped throughout.
2. **Re-implement (extend) the Plan Item Editor and finance-confirmation drawer** to recognize `Plan Need Allocation`-sourced items, not just `Plan Demand Allocation`-sourced ones. Currently a Need-sourced item would be invisible in both.
3. **Build a Budget-side consumer for the new contract**, even if it's intentionally a no-op/read path per the ledger's "no reservation from a Need" rule — right now Budget has literally no awareness `Departmental Need` or `Plan Need Allocation` exist.
4. **Fix the `get_workspace` whitelist bug** — this blocks the canonical page from working in any browser today; it's a small fix (whitelist the method properly) but currently makes NDS-G03's "Done" status of the live page false.
5. **Wire the seed orchestrator** (`run_kentender_mvp_v1`) to call `upsert_departmental_needs()` — right now a genuinely fresh environment gets legacy Demand fixtures, not the NDS ones, contradicting AC-018 and the clean-build mandate itself.
6. **Only then** execute NDS-G05/NDS-RET-001/002: delete the `demands/` doctype tree, `procurement_lifecycle/demand_module_gate.py` and the shim files, the `ensure_demands_*` patches (replace with a one-time teardown patch, following the existing `mvp1_teardown_retire_demand_intake_pre_sync.py` precedent), the legacy hooks.py asset/route entries, the `Demands` Module Def, Procurement Home's Demand-based widgets, Budget's `_demand_context()`/`dia_budget_control.py` shim code, Strategy's `Demand`-reading dashboard code, and the ~35 + 14 legacy test files. `docs/STD_MODULE_POC_RETIRED.md` is a usable template for doing this as an archive-and-swap rather than a raw delete.

Also worth fixing opportunistically: the Core G04 test failure (`authorize_support_record_view` not raising `PermissionError` for Administrator) is a real, currently-broken guard that AC-010 and the audited-support-access story for *both* Departmental Needs and the rest of the app depend on — it isn't specific to this module but it's on the critical path for AC-010 to genuinely close.

## 6. Gaps not visible from the tracker at all

- Departmental Review Delegate and Accounting Officer roles are registered but have zero seeded personas/profiles/tests — entirely unexercised code paths (AC-005, role table §7).
- No structural (as opposed to by-omission) test exists proving a Need can never reach a Requisition/Tender (AC-015) or that acceptance creates zero financial side effects (AC-007) — both currently true only because the code that would do those things was never written, which is fragile as a long-term guarantee.
- 4 of 5 Playwright specs for the live workspace have never been run at all (no artifacts), despite NDS-G03 listing "responsive, keyboard, accessibility... evidence remains" as if only breadth were missing — one of the five that *was* run failed outright.
