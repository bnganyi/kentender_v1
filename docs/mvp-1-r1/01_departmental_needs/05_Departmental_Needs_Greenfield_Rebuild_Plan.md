# Departmental Needs greenfield rebuild — plan

**Authority:** `04_Departmental_Needs_MVP1_R1_Audit_Report.md` (19 August 2026) and `NDS-CHG-001 v0.2`
**Supersedes:** the patch-based retirement approach implied by NDS-RET-001/NDS-RET-002 in `03_Departmental_Needs_Implementation_Tracker.md`. This is not production; no compatibility layer, no teardown patch, no dual contract.
**Companion document:** `06_Departmental_Needs_Greenfield_Rebuild_Tracker.md` — durable row-level tracker for executing this plan.

## Locked decisions

| Decision | Outcome |
|---|---|
| Legacy code disposition | **Delete**, not archive. `git rm`. Git history is the archive; nothing is kept under an `archive/` path or behind a feature flag. |
| Retirement mechanism | **No new patch.** Remove the existing re-provisioning patches (`ensure_demands_doctypes.py`, `ensure_demands_roles.py`, `ensure_demands_module_def.py`) from `patches.txt` and delete the patch files themselves. Do not write a teardown patch to migrate old data — there is no data worth preserving. |
| Environment | Destructive reset. Dev/test sites are dropped and reinstalled fresh, not migrated forward from a state that ever had `Demand` records. |
| Contract count | One. Every rebuilt surface (Planning UI, Plan Item Editor, finance drawer, Budget, Strategy, Procurement Home) reads/writes `Departmental Need` / `Plan Need Allocation` only. No `demand_doctype_available()`-style existence gate anywhere in the rebuilt code — if a gate like that appears in a diff, that's a signal the deletion wasn't actually completed. |
| Test suite | Delete legacy Demand tests outright (~35 Python files, 14 Playwright specs, `planning-add-demand.spec.ts`). Do not keep them skipped or excluded — they test code that no longer exists. |
| Strategy/Procurement Home Demand-derived dashboards | Dropped outright (PVC treatment tracking, funding-headroom display, pipeline widgets). No replacement is built and no dependency on `Departmental Need`/`Plan Need Allocation` is introduced into `kentender_strategy` or `procurement_home`. |

## Phases

### Phase 0 — Baseline
Tag or note the current commit as the pre-rebuild baseline (informational only — no archive branch needed since nothing is being preserved). Confirm the audit report's file inventory is still accurate immediately before starting (the codebase may have moved since 19 Aug).

### Phase 1 — Delete legacy Demands code (kentender_procurement)
Remove, in one coherent change:
- `kentender_procurement/kentender_procurement/demands/` in full (doctypes, services, pages, seeds, tests, `api.py`, `__init__.py`).
- `kentender_procurement/kentender_procurement/procurement_planning/doctype/plan_demand_allocation/`.
- `procurement_planning/services/list_eligible_demands.py`, `add_demand_to_plan.py`, `demand_financial_year.py`.
- `procurement_planning/tests/test_list_eligible_demands.py`, `test_add_demand_to_plan_gate04.py`.
- `procurement_lifecycle/demand_module_gate.py`, `legacy_demand_seed_shim.py`, `legacy_demand_codes.py`, `demand_approval_handoff.py`, `demand_journey_bootstrap.py`, `demand_planning_status.py`, and their tests under `procurement_lifecycle/tests/`.
- `public/js/demands_ui_fixtures/`, `demand_workspace.js`, `demands_live_bind.js`, `planning_demand_dialog.js`, `planning_ui_fixtures/add_demand_dialog.js`.
- `public/css/demands_workspace.css`, `demands_record_chrome.css`, `demands_form.css`, `demands_review.css`, `demands_detail.css`, `demands_performance.css`.
- `tests/ui/smoke/demands/` (14 specs) and `tests/ui/smoke/planning/planning-add-demand.spec.ts`.

### Phase 2 — Remove legacy provisioning
- `kentender_procurement/kentender_procurement/hooks.py`: remove the CSS/JS include lines and the `page_js` route entries (`demands-workspace`, `demand-form`, `demand-review`, `demand-detail`, `demand-performance`) added in Phase 1's deleted files.
- `kentender_procurement/kentender_procurement/patches.txt`: remove `ensure_demands_module_def`, `ensure_demands_doctypes`, `ensure_demands_roles` lines; delete the three patch files. Leave `mvp1_teardown_retire_demand_intake_pre_sync.py` alone (it retires a different, already-gone predecessor module and is orthogonal).
- `kentender_procurement/kentender_procurement/modules.txt`: remove the `Demands` line, keep `Departmental Needs`.
- `kentender_core/kentender_core/stitch_desk_chrome_registry.py:197`: rename the `kt-pln-ui03-add-demand` test id to reflect the Need-based flow once Phase 3's new dialog exists.

### Phase 3 — Re-implement dependent surfaces against the new (only) contract
- **Planning UI**: new "Add from Departmental Need" dialog calling `list_eligible_needs` / `allocate_need_lines`, replacing the deleted `planning_demand_dialog.js`. This is new UI work, not a port.
- **Plan Item Editor / finance drawer** (`get_plan_item_editor.py`, `plan_item_finance.py`): rebuild their allocation queries against `Plan Need Allocation` only. Since `Plan Demand Allocation` no longer exists after Phase 1, these files lose their dual-branch complexity rather than gain more.
- **Plan approval / removal** (`approve_plan_version.py`, `remove_plan_item.py`): drop the `Plan Demand Allocation` activation/reversal branches; `activate_need_allocations()` / `reverse_need_allocations()` become the sole path.
- **Budget**: implement a real consumer of `Plan Need Allocation` for whatever funding-confirmation step the ledger authorizes at the Planning stage, replacing `_demand_context()` / `_demand_context_fallback()` / `demand_doctype_available()` in `budget_check_reserve_contracts.py` and the Demand-keyed idempotency logic in `dia_budget_control.py`. Update `budget_live_bind.js`'s rendering (`demand_code` → the Need-based equivalent) and `budget_api.py`'s whitelisted kwargs.
- **Strategy** (`strategy_performance.py`, `strategy_contracts.py`) and **Procurement Home** (`home_pipeline.py`, `home_actions.py`, `seed_home_demo.py`): **drop the Demand-derived widgets outright — do not rebuild.** Decided 19 Aug 2026: no replacement dashboard/pipeline widget is introduced. The greenfield Departmental Needs implementation must not take on a dependency from Strategy or Procurement Home, and must not expose anything new for them to depend on.
- Update the seeds these surfaces depend on: `kentender_budget/seeds/budget_activity_test_fixture.py`, `kentender_budget/seeds/kentender_mvp_v1_portfolio.py`, `kentender_strategy/seeds/moh_downstream_usage.py` — replace `demand_code`/`TEST_DEMAND_CODE`-keyed fixtures with Departmental Need equivalents.
- Rewrite the cross-app tests that exercised the old wiring: `test_dem_int_009_budget_demand_context.py`, `test_budget_downstream_usage.py`, `test_budget_check_reserve.py`, `test_budget_funding_lifecycle.py`, `test_budget_revisions.py`, `test_budget_audit.py`, `test_dem_int_008_strategy_pvc_adoption.py`, `test_strategy_downstream_usage.py`, `test_strategy_mvp1_ac_matrix.py` — either against the new contract or delete if the scenario no longer applies.

### Phase 4 — Fix the concrete defects found in the audit
- Whitelist `kentender_procurement.departmental_needs.services.workspace.get_workspace` properly so `/desk/departmental-needs` renders in a real browser (currently fails with "Method Not Allowed").
- Wire `kentender_core/kentender_core/seeds/kentender_mvp_v1/orchestrator.py::run_kentender_mvp_v1` to call `upsert_departmental_needs()` instead of (deleted) `upsert_demands()`.
- Fix `authorize_support_record_view` so `test_authorization_gate04.py::test_diagnostic_is_read_only_and_support_projection_is_explicit_and_audited` passes — Administrator must get `PermissionError` through the unscoped path. This is a Core bug, not Demands-specific, but it blocks AC-010 and is cheap to fix while this area is open.

### Phase 5 — Reset and validate
- Drop and reinstall the dev site (no migration path from a Demand-containing database).
- Fresh `bench migrate`.
- Run the seed orchestrator; confirm the exact MOH fixture (3 Needs, 3 personas, PLN-MOH-2027-001 / PPI-MOH-2027-021 allocation) is produced without manual intervention.
- Run the full Python test suite for `departmental_needs`, `procurement_planning`, `kentender_budget`, `kentender_strategy`, and Core authorization gates 01-04 — expect 27/27 on gate04 this time.
- Run all 5 `departmental-needs-workspace.spec.ts` Playwright tests (not just the 1 that ran previously) plus the rebuilt Planning UI specs.
- Confirm `bench build --app kentender_procurement` is clean.

### Phase 6 — Close acceptance criteria
Re-run the NDS-AC-001..019 verification from the audit report against the rebuilt state. Update `03_Departmental_Needs_Implementation_Tracker.md`'s NDS-G05 row and the acceptance-evidence table to reflect the real (not self-reported) outcome, or supersede it with a closing note pointing at the rebuild tracker.

## Sequencing note

Phases 1 and 2 can proceed immediately since there's no live-traffic constraint — delete first, then the compile/import errors from anything still referencing the deleted code become the exact worklist for Phase 3. Do not attempt to keep the app in a runnable state between Phase 1 and Phase 3; treat the whole Phase 1-4 span as one change.
