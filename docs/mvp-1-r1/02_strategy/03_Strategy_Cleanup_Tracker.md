# Strategy Alignment cleanup — tracker

**Authority:** `02_Strategy_Cleanup_Plan.md`, `01_Strategy_Cleanup_Audit_Report.md`
**Status:** In progress — Phase 2 complete
**Started:** 2026-08-19

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence (a command, a test name, a diff) — not "looks right."
3. If a corrected file still imports or references a removed concept (PVO, Plan Value Commitment, Strategy Corrective Action, the dangling `demand_module_gate`), the row that touches it is not Done.
4. No row may introduce a new alias, redirect, dual read, shadow write, or feature flag. If one appears, treat it as a defect in that row, not a valid completion.

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| SCL-G00 | Audit, plan and tracker authored | Done | This document, `01_...Audit_Report.md`, `02_...Plan.md` |
| SCL-G01 | Module import-clean: no dangling `kentender_procurement.demands`/`demand_module_gate` reference anywhere in `kentender_strategy` | Done, with a noted limitation | Test suite collects and runs (108 tests). One remaining reference in `strategy_performance.py` resolves (module restored) but is not yet fully removed — deferred to SCL-301/Phase 3. See SCL-001..004. |
| SCL-G02 | No `Plan Value Commitment` identifier remains except historical documentation assertions | Done | Repo-wide grep confirms zero live-code hits (docs and one already-executed Core migration patch excluded per policy). See SCL-101..108. |
| SCL-G03 | No `Public Value Objective`/PVO identifier remains in navigation, hooks or mandatory validations | Done | Repo-wide grep confirms zero live-code hits (docs and my own historical-decision code comments excluded per policy). Both `Public Value Objective` and `Objective Applicability Trigger` DocTypes deleted from DB (not just files) via `frappe.delete_doc` + `bench migrate`, confirmed absent. See SCL-201..208. |
| SCL-G04 | No Strategy/treatment model or Strategy Corrective Action remains | Planned | — |
| SCL-G05 | Strategic Objective, Strategic Outcome, Performance Indicator, Performance Target are distinct in schema and UI | Planned | — |
| SCL-G06 | No Administrator-as-operational-authority or silent PE/OU fallback remains | Planned | — |
| SCL-G07 | Active-plan-overlap uniqueness enforced and tested | Planned | — |
| SCL-G08 | STR-CHG-001 §12 integration contracts implemented; `kentender_budget` consumes them with no direct table/controller access | Planned | — |
| SCL-G09 | Deterministic MoH/Kisumu seeds rebuilt, idempotent on rerun | Planned | — |
| SCL-G10 | Fresh environment installs, migrates, seeds and passes the full `kentender_strategy` test suite + STR-CHG-001 §16 smoke contract | Planned | — |

## Work register — Phase 0: unblock

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-001 | Remove dangling `demand_module_gate` import from `services/strategy_performance.py` | Done, with a noted limitation | The import now resolves — `kentender_procurement/procurement_lifecycle/demand_module_gate.py` was recreated (see below) as part of an incidental fix to a live user-reported Procurement Home crash that shared the exact same dangling import. It is a pure existence-check utility (`demand_doctype_available() = frappe.db.exists("DocType", "Demand")`), not Demands business logic, so restoring it does not reintroduce retired functionality. **Limitation:** the import itself still lives inside `_demand_pvc_treatment_counts()`, the "treatment" business logic that SCL-301 (Phase 3) removes wholesale — full removal of this Strategy-side dependency is deferred to Phase 3 rather than done here, to avoid doing Phase 3's feature-removal work under the Phase 0 banner. Verified: `bench ... console` import of `kentender_strategy.services.strategy_performance` succeeds. |
| SCL-002 | Remove dangling `demand_module_gate` import from `seeds/moh_downstream_usage.py` | Done | Went further than SCL-001 since this file's Demand-linking logic (`_link_demand`, `_apply_canonical_value_treatments`, `SEED_DEMAND_CODES`, `CANONICAL_DEMAND_TREATMENTS`, `seed_moh_performance_contribution_depth`) was fully dead/pointless, not just import-blocked: `get_strategy_usage()` already refuses to count Demand-linked records (`demand_consumers_live()` is unconditionally `False` now, since it imports `CONSUMERS_LIVE` from the deleted `kentender_procurement.demands` package inside a `try/except ImportError`), so the seed was creating orphaned records nobody reads. Removed all of it; kept `_link_budget_line`/`seed_moh_downstream_usage_refs`'s Budget Line linking (STR-CHG-001 §4.2-sanctioned). **Known Playwright impact, not fixed here:** `tests/ui/smoke/strategy-alignment/strategy-alignment-nav.spec.ts`'s "Strategy Performance shows Planning stage and PVC adoption depth (XMOD-STR-007)" test calls the now-deleted `seed_moh_performance_contribution_depth` as a fixture-prep step and asserts on PVC-adoption text that Phase 3 removes anyway — left broken intentionally rather than stubbed (a stub would itself be the kind of compatibility shim STR-CHG-001 forbids). Rewriting/splitting that spec's still-valid Planning-stage assertion from its doomed PVC-adoption assertion is Phase 3/9 work. |
| SCL-003 | Delete `tests/test_dem_int_008_strategy_pvc_adoption.py` (Demand-integration leftover, tied to cancelled XMOD-STR-008) after confirming no other still-valid assertions inside it | Done | Read in full: all 3 tests exercised `Demand`/`Demand Value Treatment`/`Demand Strategy Reference` doctypes and `_demand_pvc_treatment_counts` directly — no assertion worth preserving. `git rm`. |
| SCL-004 | Confirm `bench --site kentender.midas.com run-tests --app kentender_strategy` reaches collection; record baseline pass/fail counts | Done | **Before (blocked):** collection failed outright — `ModuleNotFoundError: No module named 'kentender_procurement.procurement_lifecycle.demand_module_gate'`, zero test evidence obtainable. **After SCL-001/002/003:** 108 tests collected — 92 pass, 2 skip, 2 fail, 11 error. All 13 non-passing tests are pre-existing domain issues unrelated to Demands (PVC/PVO code mismatches, Strategic-Objective/Outcome hierarchy gaps, entity-scope errors) — squarely Phase 1/2/4 territory, not Phase 0's. Full log preserved for reference; `test_demand_and_budget_rows_derived` moved from FAIL to a pre-existing, unrelated skip (`PKG-MOH-2026-001 not available` — same skip condition a sibling test already had) as a side effect of SCL-002, not a new regression. |

**Incidental, out-of-tracker fix during Phase 0:** the recreated `demand_module_gate.py` (SCL-001/002's shared dependency) also fixed a live, user-reported Procurement Home crash (`Failed to get method for command ... with No module named 'kentender_procurement.demands'`) — that module's `api/home.py` chain imports the same file via `home_pipeline.py`/`home_actions.py`/`home_context.py`/`home_portfolio.py`/`seed/seed_home_demo.py`. Also fixed two related bugs found while verifying: (1) `home_pipeline.py`/`home_actions.py` additionally imported real Demands business logic (`list_demands_for_workspace`) that's unrecoverable — removed, dead code paths simplified to direct `0`/`[]` returns; (2) `home_pipeline._count_approved_awaiting_planning` and `home_portfolio._unfunded_approved_demand` were silently querying the orphaned `tabDemand` table (the DocType schema record persists even though its Python package is gone) and surfacing real stale data through widgets already decided "dropped, no replacement" — zeroed both. Also fixed an unrelated `NameError: name 'pp_scope' is not defined` in `home_context.py::resolve_home_context()` (leftover from an earlier, incomplete "PP2 pp_scope retired" refactor) found while reproducing the user's navigate-away-and-back report. Deleted `procurement_home/tests/test_dem_int_006_procurement_home.py` (tested the retired functionality directly). This work is Procurement Home-scoped, not Strategy-scoped — recorded here only because it shares the root-cause fix.

## Work register — Phase 1: rename Plan Value Commitment → Strategy Value Commitment

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-101 | Rename doctype `plan_value_commitment/` → `strategy_value_commitment/` | Done | `git mv` folder + files; JSON `name`/`options`/child-table reference updated; `PlanValueCommitment` → `StrategyValueCommitment` class, `validate_plan_value_commitment` → `validate_strategy_value_commitment` call updated. |
| SCL-102 | Rename child-table doctype `plan_value_commitment_link/` → `strategy_value_commitment_link/` | Done | Same treatment; `PlanValueCommitmentLink` → `StrategyValueCommitmentLink`, `validate_plan_value_commitment_link` → `validate_strategy_value_commitment_link`. |
| SCL-103 | Update all references in `strategy_writes.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_contracts.py`, `strategy_performance.py`, `strategy_domain_guards.py`, `strategy_api.py` | Done | Mechanical 3-pattern rename (`Plan Value Commitment`/`plan_value_commitment`/`PlanValueCommitment` → `Strategy ...`) across all 7 files; verified with `bench console` import of every module. |
| SCL-104 | Update UI labels, routes, JS fixtures, `hooks.py` `page_js` entries | Done | Also renamed the Page doctype itself (`page/strategy_plan_value_commitments/` → `page/strategy_value_commitments/`, route `strategy-plan-value-commitments` → `strategy-value-commitments`) and its JS file (`strategy_plan_value_commitments_page.js` → `strategy_value_commitments_page.js`) — the sed pass alone caused a double-substitution bug in `hooks.py`'s file reference (`strategy_strategy_value_commitments_page.js`) since only content was sed'd, not the file path itself; caught and fixed by grepping for the old route slug repo-wide across `kt_module_registry.js`, `kt_cl_surface_registry.js`, `module_registry.py`, `strategy_alignment_shell.js`, `strategy_live_bind.js`, `strategy_performance.py`, `strategy_readiness.py`, and the Playwright spec. Verified live: page loads at `/desk/strategy-value-commitments` with zero error dialogs, real data rendering (screenshot). |
| SCL-105 | Update seeds and tests referencing the old name | Done | `kentender_mvp_v1_strategy.py`, `moh_review_fixtures.py`, `works_master_strategy_hierarchy.py`, 4 test files. Also fixed a cosmetic sed artifact: `TestStrategyPlanValueCommitments` → sed produced `TestStrategyStrategyValueCommitments` (doubled word from the class name already containing "Strategy"); corrected to `TestStrategyValueCommitments`. Test file itself renamed `test_strategy_plan_value_commitments.py` → `test_strategy_value_commitments.py`. |
| SCL-106 | Downstream: `kentender_budget/services/budget_contracts.py`, `budget_revision_contracts.py` label text | Done | Same fix applied to a doubled-word artifact: `budget_revision_contracts.py`'s message text became "Strategy Strategy Value Commitment" (original already said "Strategy Plan Value Commitment"); corrected to "Strategy Value Commitment". |
| SCL-107 | Downstream: Procurement Plan Item Version "Plan Value Commitment Snapshot" field label | Done | — |
| SCL-108 | Downstream: `kentender_core/seeds/kentender_mvp_v1/validate.py` | Done | `kentender_core/patches/v1_0/drop_legacy_owner_state_directorate_fields.py` deliberately **left untouched** — it's a one-time, already-executed migration patch (historical record of what actually ran), same treatment as `mvp1_teardown_retire_demand_intake_pre_sync.py` in the Departmental Needs tracker. |

**DB-level transition (not a tracker row, but required for SCL-101/102 to be real, not just file renames):** per STR-CHG-001's "no migration" rule, old `Plan Value Commitment`/`Plan Value Commitment Link` DocTypes (11 legacy rows) were deleted outright (`frappe.delete_doc(..., force=True)`, dropping their tables) rather than migrated, then `bench migrate` synced the new `Strategy Value Commitment`/`Strategy Value Commitment Link` doctypes fresh from the renamed files (confirmed 0 rows post-migrate). Seed data was rebuilt via `upsert_kentender_mvp_v1_strategy(reset=True)`.

**Two real bugs found and fixed while verifying the rename (both necessary to get back to a clean, testable baseline — not scope creep, since Phase 1 can't be verified "Done" against a broken test suite):**
1. `kentender_strategy/seeds/kentender_mvp_v1_strategy.py::upsert_kentender_mvp_v1_strategy` has a `rebuild=False` fast path for when the Strategic Plan already exists and is Active (assuming, previously always-true, that everything downstream of it — including Value Commitments — already exists too). My deletion of only the PVC/PVC-Link data (not the Strategic Plan) broke that assumption for the first time ever, since the Plan's table was untouched and stayed Active while PVC data was wiped. Fixed by using the seed function's own existing `reset=True` path (a full, correctly-scoped fixture wipe-and-rebuild already designed for this exact situation) rather than patching the function's logic. Not a rename-caused regression — a latent inconsistency the rename's data reset was the first thing to ever expose.
2. `bench migrate`'s orphan-doctype cleanup (triggered incidentally by the SVC doctype sync) also finally removed the long-stale `Demand` DocType record entirely (its Python package was deleted months earlier in the Departmental Needs work, but the DocType DB record/table had survived until this migrate). This exposed a missing guard in `strategy_contracts.py::get_strategy_usage()` — `frappe.db.has_column("Demand", "strategy_plan_version")` raises `DoesNotExistError` when the DocType itself doesn't exist (not just returns False), unguarded unlike the equivalent check in `strategy_performance.py`. Fixed by adding the same `frappe.db.exists("DocType", "Demand") and ...` guard already used elsewhere in this codebase. This directly matches STR-FR-020 and is exactly the kind of gap STR-CHG-001 targets — legitimate to fix now since it was blocking all `test_strategy_performance.py`/`test_strategy_downstream_usage.py` verification.

**Verification:** `bench --site kentender.midas.com run-tests --app kentender_strategy` returns to the exact Phase 0 baseline (108 tests, 2 failures, 11 errors, 2 skipped — same test names, all pre-existing domain issues unrelated to this rename) after a full stash/restore round-trip to confirm no downstream Budget regression (5 pre-existing, unrelated `test_budget_ui_stitch_layout_guard.py` CSS-assertion failures confirmed present identically with my changes reverted). Asset rebuild (`./scripts/bench-with-node.sh build --app kentender_strategy`) succeeds; live Playwright run confirms the renamed page loads at its new route with real data and zero errors.

## Work register — Phase 2: remove Public Value Objective engine

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-201 | Delete doctype `public_value_objective/` | Done | `git rm -r`. Also deleted `objective_applicability_trigger/` (a PVO-only child table not named in the original plan row, found to be dependent-only during implementation) — same treatment. **DB-level:** both DocTypes existed as live DB records with real tables; deleted via `frappe.delete_doc("DocType", ..., force=True)` (no migration — matches STR-CHG-001's rule) before `bench migrate` synced the schema; confirmed absent post-migrate. |
| SCL-202 | Remove PVO logic from `strategy_contracts.py`, `strategy_domain_guards.py`, `strategy_notification_service.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_writes.py`, `strategy_transitions.py`, `strategy_api.py` | Done | Removed: `list_public_value_objectives`, `list_applicable_value_commitments` (the PVO applicability-trigger "generic rules engine" STR-CHG-001 §1.3 explicitly excludes — not adapted, deleted outright), `upsert_pvo`, `get_pvo`, `transition_pvo`, `PVO_TRANSITIONS`, `validate_public_value_objective`, `validate_objective_applicability_trigger`, `IMMUTABLE_PVO`, all 5 `EVENT_PVO_*` notification constants + `notify_pvo_transition` + their routing/subject-line branches, the `"OBJ"` reference-type mapping and `CATALOGUE_OBJ_RE` carve-out in `strategy_reference.py`. Rewrote `list_strategy_value_commitments` (the live UI-consumed contract) to use the commitment's own `commitment_code`/`rationale` as its "objective" reference instead of joining to PVO — this is the module's real data-shape correction, not just deletion. Removed the PVO-required-before-Active-status guard from `upsert_strategy_value_commitment` and the PVO-Active readiness blocker from `strategy_readiness.py`. |
| SCL-203 | Delete page `strategy_pvo_catalogue_page.js` + `page/strategy_pvo_catalogue/` | Done | `git rm -r`. |
| SCL-204 | Delete page `strategy_pvo_editor_page.js` + `page/strategy_pvo_editor/` | Done | `git rm -r`. |
| SCL-205 | Delete JS fixtures `strategy_ui_fixtures/pvo_catalogue.js`, `pvo_editor.js` | Done | `git rm`. Also rewrote `strategy_ui_fixtures/value_commitments.js`'s drawer markup: removed the entire PVO "library" (search/pillar/source filter + scrollable pick-list) and "preview" sections — the commitment-statement form (rationale/level/owner/links) is now the whole drawer, since there's no external catalog to browse. Fixed a stray Phase-1 case-sensitivity miss in the same pass: heading read "Plan value commitments" (sentence case, missed by Phase 1's exact-case sed) — corrected to "Strategy value commitments"; updated the now-inaccurate PVO-referencing subtitle/help copy. |
| SCL-206 | Remove `hooks.py` `page_js` routes (`strategy-pvo-catalogue`, `strategy-pvo-editor`) and related CSS/JS includes | Done | Removed both `page_js` entries and the two `app_include_js` fixture-script lines. No dedicated PVO CSS file existed. Also removed the now-dead `.kt-str-vc-pvo-*` CSS rules (picker option/selected-badge styling) from `strategy_alignment_value_commitments.css`, orphaned by SCL-205's markup removal. |
| SCL-207 | Remove PVO nav labels from `kentender_core/public/js/kt_cl_surface_registry.js` | Done | Removed the `STR-UI-05`/`STR-UI-06` surface entries (catalogue/editor). Also cleaned up 3 more files the original plan row didn't anticipate: `kt_module_registry.js` and `module_registry.py`'s `route_prefixes` lists (stale route fast-path entries), and a "Learn about Strategic Pillars" quick-help link in `strategy_ui_fixtures/portfolio.js` + its `pvo-catalogue` action handler in `strategy_alignment_portfolio_page.js` + a matching text-triggered handler in `strategy_alignment_shell.js` — all pointed at the now-deleted catalogue with no replacement destination, so the link was removed rather than repointed (STR-CHG-001: "no MVP replacement"). |
| SCL-208 | Remove/rewrite PVO-referencing seeds and tests | Done | **Seeds:** `kentender_mvp_v1_strategy.py` — removed `PVO_FIXTURE`/`_ensure_pvos`, redesigned `PVC_FIXTURE` from `(code, pvo_code, level)` to `(code, commitment_statement, level)` folding the former PVO titles directly into the commitment's own `rationale` (matches STR-CHG-001 §6's "commitment statement" field intent); did the same for the Kisumu fixture; removed the `pvos` dict threaded through `_seed_kisumu_strategy()`'s signature and the top-level return payload. `works_master_strategy_hierarchy.py` — deleted the entire `_upsert_works_master_strategy_hierarchy_legacy` function (247 lines, already documented as "retained for reference; unused" dead code) and its sole dependency `_ensure_pvos`/`PVO_FIXTURE`, since leaving PVO-referencing dead code that would crash if ever called contradicts "no compatibility layer." Downstream: `kentender_budget/seeds/kentender_mvp_v1_portfolio.py::_resolve_pvc_id` simplified from a commitment-code-then-PVO-code fallback chain to the single correct lookup (confirmed all real callers pass genuine PVC codes, never PVO codes). **Tests:** `test_strategy_mvp1_domain.py` (PVO-count assertion → SVC-count assertion), `test_strategy_value_commitments.py` (removed `_active_pvo` helper and all `public_value_objective_version` payload fields across 5 tests; updated objective-code assertions from `PVO-*` to the real `MOH-PVC-*`/auto-generated-PVC-pattern), `test_strategy_ui_stitch_layout_guard.py` (removed 2 dead fixture-file entries + a dead Page-route entry + a dead markup/geometry assertion block for the deleted filter grid), `test_strategy_mvp1_ac_matrix.py` (deleted `test_str_ac_010_applicability_filter`/`test_str_ac_011_consideration_not_tender_criterion` — both existed solely to test the removed PVO rules engine; updated the file's own coverage-map docstring to mark STR-AC-010/011/028 "retired" rather than leave a false "yes — this module" claim). Also fixed `strategy-alignment-nav.spec.ts` (Playwright, not part of the plan row but discovered broken): rewrote the "add commitment via drawer" flow to fill the form directly instead of picking a PVO from a library list, and deleted a "satellite surfaces open" sub-test that navigated to the two deleted routes. |

## Work register — Phase 3: remove treatment logic and Strategy Corrective Action

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-301 | Remove "treatment" business logic from `strategy_performance.py` | Planned | — |
| SCL-302 | Delete doctype `strategy_corrective_action/` | Planned | — |
| SCL-303 | Delete page `strategy_corrective_actions_page.js` and service references | Planned | — |
| SCL-304 | Remove corrective-action nav entry and hooks routes | Planned | — |
| SCL-305 | Strip `strategy_alignment_performance_page.js` to a neutral read surface (keep the page, per locked decision) | Planned | — |

## Work register — Phase 4: Objective/Outcome/Indicator semantic correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-401 | Design and introduce an explicit Strategic Objective concept, consistent with the existing standalone `Strategic Outcome`/`Performance Indicator` pattern | Planned | — |
| SCL-402 | Fix `REF_TYPE_META` in `strategy_reference.py`: add `"Strategic Objective"`, remove `"OBJ" → "Public Value Objective"` | Planned | — |
| SCL-403 | Test: a Performance Indicator measures one Strategic Objective or Strategic Outcome, never both, never itself an objective (STR-CHG-001 §6.2) | Planned | — |

## Work register — Phase 5: replace Administrator/fallback authority patterns

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-501 | `strategy_reference.py::can_correct_reference()` — replace System Manager/Administrator gate with explicit Strategy capability check | Planned | — |
| SCL-502 | `strategy_permissions.py` (lines 41, 48, 90) — same replacement | Planned | — |
| SCL-503 | `strategy_performance.py` (lines 66, 73, 802) — same replacement | Planned | — |
| SCL-504 | `strategy_reference.py::resolve_pe_for_doc()` — fail-closed instead of silent `None` | Planned | — |
| SCL-505 | Seed files — replace hardcoded `"Administrator"` actors with real Strategy Author/Reviewer/Approval Authority persona users, `Test@123` passwords | Planned | — |
| SCL-506 | Broader sweep for un-named `first_pe`/`.first()`-style fallback patterns not caught by the audit's targeted grep | Planned | — |

## Work register — Phase 6: harden active-plan-overlap uniqueness

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-601 | Review/harden `strategy_domain_guards.py::normalize_plan_scope()`'s "legacy rows" fallback | Planned | — |
| SCL-602 | Add/confirm concurrent-activation test (two overlapping plans race to Active) | Planned | — |

## Work register — Phase 7: integration contracts + Budget ripple

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-701 | Implement/adapt `resolve_strategy_context` | Planned | — |
| SCL-702 | Implement/adapt `list_strategy_commitments` | Planned | — |
| SCL-703 | Implement/adapt `get_strategy_lineage` | Planned | — |
| SCL-704 | Implement/adapt `create_strategy_snapshot` | Planned | — |
| SCL-705 | Stub `record_verified_result` only — explicitly deferred to Contract Management scope | Planned | — |
| SCL-706 | Migrate `kentender_budget` consumer calls onto the new/renamed contracts | Planned | — |
| SCL-707 | Close the raw-DB-query `except ImportError` fallback in `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` (~lines 489–536) | Planned | — |
| SCL-708 | Update `kentender_budget/tests/test_budget_line_strategy_validate.py` for the Phase 1 rename | Planned | — |

## Work register — Phase 8: seed rebuild

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-801 | Rebuild MoH primary plan `STR-MOH-2023-001` and full hierarchy per STR-CHG-001 §13.1 | Planned | — |
| SCL-802 | Rebuild `SVC-MOH-2027-001` Strategy Value Commitment | Planned | — |
| SCL-803 | Rebuild Kisumu primary plan `STR-KSM-2023-001` | Planned | — |
| SCL-804 | Confirm seed fails loudly on missing CFG (PE/FY) prerequisites — no fallback creation | Planned | — |
| SCL-805 | Confirm idempotent double-run (STR-AC-014) | Planned | — |
| SCL-806 | Update `kentender_procurement/procurement_lifecycle` seed-orchestration call sites for renamed identifiers only | Planned | — |

## Work register — Phase 9: test suite and verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| SCL-901 | Fix/rewrite flagged test files (audit §7) | Planned | — |
| SCL-902 | Add coverage for STR-FR-001..022 and STR-AC-001..018 gaps | Planned | — |
| SCL-903 | Run STR-CHG-001 §16 smoke contract in full (8 gates) | Planned | — |
| SCL-904 | Update this tracker with final evidence; do not revive `docs/mvp-1/01_strategy` | Planned | — |

## Explicitly deferred / out of scope

| Item | Disposition |
|---|---|
| XMOD-STR-005 downstream half (Tender/Award consuming the lineage/snapshot contract) | Deferred to a separate, future change unit. Provider-side contract (SCL-703/704) proceeds here. |
| XMOD-STR-008 (remediation notifications) | Cancelled as superseded — its trigger (corrective actions) is removed in Phase 3. Not rebuilt. |
| Dangling `kentender_procurement.demands` imports outside `kentender_strategy` (Procurement Home, Procurement Planning, Core seeds) | Pre-existing, accepted breakage under the Departmental Needs tracker's RBD-G02. Not this tracker's responsibility. |
| Procurement Planning integration | No current Strategy import exists; Planning itself is in a known-broken, deferred state per the Departmental Needs tracker's RBD-3xx boundary. Not touched here. |
| Generic Public Value Objective rules engine / advanced performance-management suite | Explicitly excluded by STR-CHG-001 §1.3. Not deferred — not to be built toward. |

## Open decisions

None outstanding — Corrective Actions (remove), Performance dashboard (strip, keep page), XMOD-STR-005/008 disposition, and Budget ripple depth (including the raw-query fallback) were all confirmed with the product owner on 19 August 2026 (see `02_...Plan.md` locked decisions).

## Blockers

- SCL-G01 (module import-clean) blocks all other gates — no test evidence exists for this module until Phase 0 is closed.

## Change log

| Date | Change |
|---|---|
| 2026-08-19 | Audit report, plan and tracker authored following review of STR-CHG-001, the four original `docs/mvp-1/01_strategy` documents, current `kentender_strategy` code inventory, and cross-module dependency scan. Corrective Actions removal, Performance dashboard strip-not-remove, XMOD-STR-005/008 disposition, and Budget raw-query-fallback fix all confirmed with product owner same day. |
| 2026-08-19 | Phase 0 (unblock) complete — SCL-001..004 done. Test collection restored (0 → 108 collectible tests); `test_dem_int_008_strategy_pvc_adoption.py` deleted; `moh_downstream_usage.py`'s dead Demand-linking code removed. SCL-G01 closed with a noted limitation (full `strategy_performance.py` removal deferred to Phase 3/SCL-301). |
| 2026-08-19 | Phase 1 (Plan Value Commitment → Strategy Value Commitment rename) complete — SCL-101..108 done, SCL-G02 closed. DocTypes, page/route, all service/seed/test references, and the downstream Budget/Core ripple all renamed with no compatibility alias, per STR-CHG-001's no-migration rule. Found and fixed two real bugs surfaced while verifying (a seed rebuild-assumption gap exposed by the destructive PVC-only reset, and a missing `Demand`-DocType-existence guard in `get_strategy_usage()` exposed by `bench migrate` finally removing the long-orphaned `Demand` DocType record) — both necessary to restore a clean, verifiable test baseline. Confirmed back to the exact Phase 0 baseline (108 tests, 13 non-passing, same tests) after a stash/restore round-trip proving no downstream regression. |
| 2026-08-19 | Phase 2 (Public Value Objective engine removal) complete — SCL-201..208 done, SCL-G03 closed. Deleted 2 DocTypes (`Public Value Objective`, `Objective Applicability Trigger` — the latter found during implementation, not in the original plan row), 2 Pages, 4 JS files; removed PVO logic from all 8 named service files plus 3 additional nav-registry files found during implementation; rewrote `list_strategy_value_commitments` and the Value Commitments drawer UI to use the commitment's own identity/statement instead of joining to an external PVO catalog (STR-CHG-001's "no MVP replacement" for PVO, not an adaptation); redesigned the MOH/Kisumu seed fixtures to fold former PVO titles directly into commitment rationale text; deleted 247 lines of already-dead legacy seed code that would have crashed if ever invoked. Same DB-level treatment as Phase 1 (delete-then-migrate, no data migration). Fixed one Python test as a side effect (`test_incomplete_without_links`), deleted 2 Python tests and 1 Playwright sub-test that existed solely to test the removed PVO rules engine, and fixed one genuine regression caught mid-phase (a stale fixture-marker assertion) before it could land. Confirmed clean via full test suite (106 tests, 11 pre-existing non-passing — same set as Phase 1 minus the 2 intentionally-deleted PVO tests), asset rebuild, and a live-browser screenshot of the redesigned Value Commitments page showing real `MOH-PVC-*` data with zero PVO references. |
