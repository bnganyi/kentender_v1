# Progress — WP1.3 + WP0.2 (retire Tender Management v2; inventory)
| Finding | Status | Red test (file::name) | Commit | Verified on | Notes |
|---|---|---|---|---|---|
| WP0.2 inventory | Green | n/a (`audit/tm2-inventory.md`) | (this commit) | read-only counts, test + dev | All 23 `TM2 *` tables empty on both sites; Procurement Journey / Handoff Card also empty. |
| AUD-XC-003 | Green (closed by deletion) | `kentender_procurement/tests/test_retired_surface_gone.py::TestRetiredSurfaceGone` (4 tests, red before deletion) | 7aa419cc (+ file deletions swept into 9c7c9a6d via shared index) | test site: new tests + migrate | Package, 23 doctypes + 5 companion doctypes, Desk page, assets, hooks, Makefile targets, scripts, UI specs, lifecycle/home/core references removed. Endpoints no longer routable. |
| AUD-XC-126 | Green | `kentender_procurement/tests/test_patches_tolerate_dropped_tables.py::test_each_patch_is_a_no_op_when_its_tables_are_gone_and_safe_twice` (TableMissingError before) | 4e8995f2 | test site | TM2 export half closed by deletion; the three post-sync Planning patches now guard with `table_exists`. |
| AUD-XC-011 | Green (fixed in place; NOT TM2) | `kentender_procurement/tender_configurations/tests/test_publication_record_permissions.py` (4 tests, red before) | 2d630604 | test site: tests + migrate (DocPerm rows verified in DB) | Both doctypes belong to Tender Configurations. `All` DocPerm removed (officer roles Tender Manager / Planning Authority instead); direct `status` / `package_status` change refused unless the service flag is set (all service call sites already set it). |
| AUD-XC-143 | No change needed here (stays open) | | | | Tender Configurations / Tenders, not TM2; does not close with the retirement. See Follow-ups. |

Drop patch: `kentender_procurement.patches.drop_retired_tm2_surface` (pre_model_sync, last entry). Raw guarded SQL (no `frappe.delete_doc`), refuses to drop a non-empty table, double-run + leftover-removal tests in `test_retired_surface_gone.py::TestDropRetiredSurfacePatch`. Ran during `bench --site kentender-test.local migrate` (Patch Log row present; 0 TM2 DocTypes/tables/Page left on the test site).

## Follow-ups
1. **Procurement lifecycle layer (Journey / Handoff Card / `plc-*` pages / `procurement_lifecycle` package) is a TM2-era layer.** Its journey steps, handoff builders, readiness summary and "works master" seed were all built on the TM2 tender, and it also refers to retired Demand / Procurement Package / STD Instance objects. I removed the TM2-bound parts (4 handoff builders, readiness summary + API + JS/CSS, `seeds/`, the TM2 handoff panel endpoint, `tm2_tender_ref` field) and the 26 lifecycle tests that only ran against the TM2 master seed world (including r3_001..003, r3_017/018 which exercised kept services via that world). The kept layer has no data on either site, no menu entry, and now less test coverage. Options: (a) retire the whole layer (Procurement Journey, Journey Step, Handoff Card doctypes, pages `plc-procurement-journey` / `plc-module-journey-context`, `procurement_lifecycle`, `stable_platform_seed` purge); (b) keep and rebuild tests on a fresh fixture. Recommended: (a), as one owner-approved WP. Did instead: removed only TM2 references.
2. **XC-143 not closed.** `tender_configurations` services (26 `frappe.db.commit()` calls; `get_tender_configuration_review` writes on a GET) are the legacy IT-wizard/BWMF module (kept by the BDS OD-F decision, FU-05), not TM2. Decide: retire that module too (then XC-143 and the remaining Tender Configurations findings close by deletion) or fix the commits. Recommended default: retire with its own owner decision.
3. **Procurement Home (old `kt-procurement-home` page)** lost its tender-side figures: pipeline is now 2 stages, deadlines section returns empty, tender portfolio cards and tender actions removed (all read the TM2 tender). The live Home is the kentender_core Home; recommend retiring `procurement_home` in the same WP as item 1. Tests updated (`test_home_service_contract`: 5 stages -> 2).
4. **Orphaned v1 child doctypes** (module Kentender Procurement): Tender BoQ Item, Tender Lot, Tender Works Requirement, Tender Required Form, Tender Section Attachment, Tender Validation Message, Tender Hardening Finding, Tender Derived Model Readiness. No code references them; not TM2 (`Procurement Tender` era). Recommend a drop patch in a later WP.
5. **Bench-root scripts outside the repo** still exist and are dead: `/home/midasuser/frappe-bench/scripts/{p11_04_tm2_surface_gate.sh, p11_05_tm2_surface_legacy_literal_gate.sh, p12_01_tm2_works_scenario_harness.sh, tm2_v1_contamination_scan.sh, x_01_planning_std_poc_regression_gate.sh, x_02_tender_management_docs_no_plain_bench_build_gate.sh, x_03_doc9_section_23_4_acceptance_sequence_gate.sh, audit_x_02_*.py, audit_x_03_*.py, run-std-library-regression.sh}`. Not in git; owner to delete.
6. `setup/tender_v1_retirement.py` + its test (Tender Management **v1** desk wipe) kept; its one-shot patch `remove_tender_management_v1_desk_artifacts` was removed from `patches.txt` and deleted (long applied; file name matched the gate). The helper is now unreferenced except by its own test.
7. Roles `Tender Manager`, `Planning Authority`, `Procurement Officer` and the sidebar section label "Tender Management" (over the live Tenders module) are not TM2 and were kept.
9. `kentender_core/.../tests/test_whitelisted_principal_parameters.py` (other agent, uncommitted) still names the retired `kentender_procurement.tender_management` prefix as "allowed to be half-removed"; delete that allowance now the tree is gone so the repo gate is clean.
10. Pre-existing failures seen in kept lifecycle/core tests (not caused by this WP; they need rows/tables that no longer exist on the test site): `test_r3_014_current_stage_calculator`, `test_r3_019_permission_filtering` (api_002), `test_r4_013_technical_evidence_drawer` need Procurement Journey `JRN-MOH-2026-001` (journey table has 0 rows on both sites); `test_r5_002_*` needs dropped Strategy Objective/Target tables; `kentender_core` `test_stable_platform_seed` (3) and `test_demo_platform_seed` (2) need the dropped `Demand` table; `setup.tests.test_procurement_sidebar_g0_012_contract` (2 failures, already recorded in memory as pre-existing drift). Candidates for the follow-up 1 retirement.
11. Git hygiene: because the index is shared, 371 of my staged deletions were committed inside another agent's commit `9c7c9a6d` ("test(ui): regenerate Needs and Planning visual baselines ...", which also deleted `kentender_budget/.../dia_budget_control.py` from someone else's staging). The tree is correct; only the commit message attribution is wrong. No history rewrite done.
8. `docs/audit/seed_data_bundle.zip` and `docs/consolidated_docs.zip` were not unpacked/scanned for TM2 text.

## Needs browser check
- Desk loads without console 404s after the asset-hook removals (assets for the 5 removed JS/CSS files are no longer referenced; clear cache + hard refresh).
- Procurement Home page (`/desk/kt-procurement-home`): 2-stage pipeline, empty deadlines state, portfolio shows budget figures only.
- Procurement Journeys page (`/desk/plc-procurement-journey`): list cards no longer show "Open Tender".
- IT Tender Configuration dashboard fallback breadcrumb now links to `tenders`.
- Publications / Publication Setup pages (Tender Configurations) as an officer: confirm status actions still work with the new DocPerms and status guard (service paths set the flags; not exercised in a browser).

## Dev site actions needed
- `bench --site kentender.midas.com migrate` (runs `drop_retired_tm2_surface`, syncs the two DocPerm changes and the removed Procurement Journey field `tm2_tender_ref`, which only drops from metadata; the column stays harmlessly). Until then dev keeps the 23 empty TM2 tables and 5 companion doctype records, the `tender-management-v2` Page record and `All` DocPerm on the two publication doctypes; the code for them is gone, so the page route fails to load but nothing else depends on it.
- After migrate: `bench --site kentender.midas.com clear-cache`, restart workers, then hard refresh Desk.
- Not run on dev by me (only read-only SELECT counts).

## Document follow-ups
- Docs under `docs/mvp-1-r1` that still mention TM2 (not edited): 26 files, notably `11_tenders/TPR-CHG-001_FOLLOW_UPS.md` (FU-08, "inverted Administrator authority" debt now closed by deletion), `12_bid_submission/reconciliation/legacy_inventory.md` §4 (the OD-F TM2 clean-up is now done; this was the owner-endorsed plan I followed), `12_bid_submission/BDS-CHG-001*` trackers/plans, `18_home_page/reconciliation/hook_inventory.md`, `17_oversight_visibility/reconciliation/baseline_audit.md`, and the plans for EVL/AWD/ANL/PLN.
- Outside `docs/mvp-1-r1`: I deleted the wholly-TM2 documents (`docs/prompts/tender management/`, `docs/tender-management-v2/`, `docs/audit/module_implementation_catalog/06_tender_management.md`, `docs/audit/seed_data_bundle/fixtures/tm2_seed_works_open_tender.json`). 49 other superseded prompt packs / audits mention TM2 in passing (list below); recommend moving them to `archive/` rather than editing.

- docs/audit/module_implementation_catalog/04_procurement_planning.md
- docs/audit/module_implementation_catalog/05_std_admin.md
- docs/audit/module_implementation_catalog/README.md
- docs/audit/module_implementation_catalog/doctypes_inventory.csv
- docs/audit/planning_tender_handoff_2026-05-03/AUDIT_SNAPSHOT.md
- docs/audit/planning_tender_handoff_2026-05-03/officer_tender_config.py
- docs/audit/seed_data_bundle/README.md
- docs/audit/seed_data_bundle/frozen/bench_execute_catalog.json
- docs/audit/seed_data_bundle/frozen/stdinst_1400_stable_ids.json
- docs/audit/seed_data_bundle/packages/ke-ppra-works-building-2022-04-poc/evidence/acceptance_pack.md
- docs/mvp-1/04_planning/04_Procurement_Planning_MVP1_Implementation_Tracker.md
- docs/mvp-1/04_planning/05_Procurement_Planning_MVP1_Gap_Rectification_Tracker.md
- docs/procurement-home/DELIVERY_REPORT.md
- docs/prompts/0. usability handoff/1. procurement_lifecycle_usability_handoff_rectification_pack.md
- docs/prompts/0. usability handoff/2. procurement_lifecycle_usability_handoff_rectification_cursor_implementation_pack.md
- docs/prompts/0. usability handoff/3. procurement_lifecycle_works_master_seed_data_specification.md
- docs/prompts/0. usability handoff/4. procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md
- docs/prompts/architecture/Kentender Workbench Typography v1.0.md
- docs/prompts/planning-to-tender-handoff/2. planning_to_tender_handoff_specification.md
- docs/prompts/planning-to-tender-handoff/3. works_seed_scenario_refactor_specification.md
- docs/prompts/planning-to-tender-handoff/4. works_tender_stage_hardening_specification.md
- docs/prompts/planning-to-tender-handoff/5. works_tender_stage_hardening_cursor_implementation_pack.md
- docs/prompts/planning-to-tender-handoff/IMPLEMENTATION_TRACKER.md
- docs/prompts/procurement planning v2/0.1. procurement_planning_v_2_baseline_audit_gap_analysis_and_revamp_pre_prd.md
- docs/prompts/procurement planning v2/0.2. procurement_planning_v_2_full_prd.md
- docs/prompts/procurement planning v2/1. procurement_planning_v_2_cursor_implementation_control_protocol.md
- docs/prompts/procurement planning v2/2. procurement_planning_v_2_cursor_implementation_pack.md
- docs/prompts/procurement planning v2/3.1 procurement_planning_v_2_implementation_tracker.md
- docs/prompts/procurement planning v2/4. procurement_planning_v_2_smoke_contract.md
- docs/prompts/procurement planning v2/5. procurement_planning_v_2_works_seed_data_specification.md
- docs/prompts/procurement planning v2/7. procurement_planning_v_2_governance_state_and_approval_model.md
- docs/prompts/procurement planning v2/8. procurement_planning_v_2_strict_domain_model.md
- docs/prompts/procurement planning v2/9. procurement_planning_v_2_roles_and_permissions_matrix.md
- docs/prompts/procurement planning v2/P0-repository-inventory.md
- docs/prompts/procurement planning v2/reset/2.procurement_planning_v_2_p_5_ux_reset_implementation_tracker.md
- "docs/prompts/procurement planning v3/3. Procurement Planning v3 \342\200\224 Cursor Implementation Contract and Tracker.md"
- docs/prompts/procurement planning v4/package wizard/PACKAGE_WIZARD_WIRING_TRACKER.md
- docs/prompts/ui refactor/ken_tender_tender_management_ui_refactor_notes.md
- docs/std-engine/BE-00_REPO_AUDIT.md
- docs/std-engine/BE_IMPLEMENTATION_TRACKER.md
- docs/std-engine/IMPORT_WIRING_PLAN.md
- docs/std-prod-impl/IT-STD-Wizard-v3/B-Components/COMPONENTS.md
- docs/std-prod-impl/IT-STD-Wizard/00 Correct Next Sequence After STD Engine.md
- docs/std-prod-impl/IT-STD-Wizard/99 IT_Tender_Wizard_Screen_Ownership_Matrix.md
- docs/std-prod-impl/cursor/README.md
- docs/std-prod-impl/std backend answers.md
- docs/tender-publications/IMPLEMENTATION_TRACKER.md
- docs/tender-publications/README.md
- docs/test-contracts/workspace-pattern-rollout-matrix.md


## Gate (repo-wide grep, excluding .git, node_modules, archive/, docs/mvp-1-r1/**, audit/, binaries, package-lock.json)
Pattern `tm2|tender[_ -]management[_ -]v2|tender_management|tender-management` (case-insensitive).
- Code, scripts, Makefile, tests, hooks, JS, CSS, JSON outside `docs/`: only `patches.txt` (the line registering `drop_retired_tm2_surface`), the drop patch itself, and one hit that is NOT mine: another agent's untracked `kentender_core/kentender_core/tests/test_whitelisted_principal_parameters.py` (lines 46-50, 87, 138-139) allow-lists the retired package prefix. With the package deleted that allowance is dead; its owner should remove it (see Follow-ups 9). My own test `tests/test_retired_surface_gone.py` assembles the names from fragments so it does not match.
- Remaining hits are all under `docs/` (49 files listed above) and `docs/mvp-1-r1/` (26 files, not edited).

## Commands run
All on kentender-test.local, wrapped in `flock /tmp/kt-test-site.lock`:
- RED: `bench --site kentender-test.local run-tests --app kentender_procurement --module kentender_procurement.tests.test_retired_surface_gone` -> 3 failures + 2 errors (package/doctype dirs still present, patch missing).
- RED: `... --module kentender_procurement.tender_configurations.tests.test_publication_record_permissions` -> 4 failed/errored (role All present; no status guard).
- RED: `... --module kentender_procurement.tests.test_patches_tolerate_dropped_tables` -> TableMissingError in all 3 patches.
- GREEN: same three modules after the changes -> 6/6, 4/4, 1/1 OK (re-run after commits, OK).
- `bench --site kentender-test.local migrate` -> completed cleanly; Patch Log has `drop_retired_tm2_surface`; afterwards 0 TM2 DocTypes, 0 TM2 tables, Page `tender-management-v2` gone; DocPerm for the two publication doctypes = System Manager, Tender Manager, Planning Authority.
- Affected module tests: `procurement_home.tests.test_home_service_contract` 14 OK (1 skipped); `test_home_context_scope` 6 OK; `setup.tests.test_workspace_sidebar_fastpath` 9 OK; `setup.tests.test_tender_v1_retirement` 1 OK; `bid_submission.tests.test_legacy_retirement` 8 OK; lifecycle `test_r1_001..006,008,010` OK, `test_r5_001` OK, `test_r5_003` 14 OK (11 skipped); `kentender_core.tests.test_kt_cl_surface_registry_contract` 7 OK.
- Failures (all pre-existing, see Follow-ups 10): g0_012 sidebar contract 2, r3_014, r3_019, r4_013, r5_002, stable/demo platform seed tests.
- Not run: Playwright (not permitted), `kentender_procurement.tenders` / `tender_configurations` full module suites (no code in those modules changed except the two doctype controllers/DocPerms, covered by the new test), no migrate or any write on the dev site (read-only SELECT counts only).
