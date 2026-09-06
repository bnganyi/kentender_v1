# STR-CHG-001 v1.7 — Strategy Alignment correction pass — tracker

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_7.md` (supersedes v1.6; §15 carries STR-AC-001..037 after KT-STD-001 v1.3 §3A added STR-AC-035..037).
**Companions:** `02_STR_Rebuild_Gap_Analysis.md`, `03_STR_Rebuild_Implementation_Plan.md`, `FOLLOW_UPS.md`, `../00_common/KenTender_SEED-001_Harmonized_End_to_End_Fixture_v1_0.md`.
**Status:** **Phases 0–9 closed on 2026-09-06.** A Strategy Author can register a usable strategy end to end on the §14 seed world in a real browser; every STR-AC row below is evidenced except the design-fidelity half of STR-AC-025 (open as FU-01).
**Started:** 2026-09-03 · **Closed:** 2026-09-06

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence (a command, a test name, a diff, a described screenshot) — not "looks right."
3. If a touched file still references a concept §1.1 or §17 prohibits (`procuring_entity_id`, `pe_fy_context`, `owner_org_unit_id`, `financial_year_id` as a fieldname, `Strategy Viewer`, `Strategy Reviewer`, `Strategy Approval Authority`, a retired lifecycle status, `STRATEGY_SCOPE_REQUIRED`, `STRATEGY_PERMISSION_DENIED`, or any disposed concept from §1.1's register), the row that touches it is not `Done`. The scan is now executable: `test_str_chg_001_v1_7_correction.TestStaticScan.test_no_retired_concept_in_executable_strategy_code` (patches and tests excluded — they legitimately name what they delete or scan for).
4. No row may introduce an alias, redirect, dual-write, compatibility shim, or parallel legacy+new surface. If one appears, treat it as a defect in that row, not a valid completion.
5. §11 (Claude Design contract) governs visual/content fidelity only. §1–10 and §12–19 govern behaviour. A row implementing behaviour from §11 content instead of §12 is a defect, not a shortcut.
6. Deletion lands in the same phase as its replacement. "Delete later" is not a valid row state.
7. A row claiming CU-3xx (commit `ccff1b80`) already covers an item must cite the specific file:line evidence, not just the commit hash.

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-09-03 | Treat this as a **correction pass**, not a rebuild from scratch. | Commit `ccff1b80` (CU-3xx) already migrated Strategy's authorization onto the site-wide URA model. `02_STR_Rebuild_Gap_Analysis.md` §2 catalogues what was done; the remaining gaps were specific and bounded. |
| 2026-09-03 | **D1 — `kentender_scope_map` registration.** Keep CU-302's decision not to register Strategy DocTypes into the map, despite §16.1's literal instruction. Documented deviation, flagged to the AUTH-ADR-001 owner as a possible spec erratum. | No OU field survives on `Strategic Plan` to name in a map entry, and the ADR's documented map shape does not match the merge code in `kentender_core.services.authorization`. DocPerm-via-URA-projection is the correct, working list gate for a site-wide role. **Retained at close (STR-405).** |
| 2026-09-03 | **D2 — `StrategyAuditEvent` (§4.6/§13).** Keep the shared `kentender_core.audit_event_service`; no dedicated Strategy doctype. Close the one real gap (exercised responsibility assignment ID) by threading the authorization decision's assignment through. | A prior decision (`strategy_audit.py`) already rejected a bespoke doctype as a duplicate mechanism, and `test_str_chg_001_phase1_domain_model.TestStrategyAuditMigratedToCoreEvent` asserts its absence. **Closed 2026-09-06 (STR-505):** every workflow event now carries `metadata.business_role` and `metadata.assignment`. |
| 2026-09-03 | **D3 — dead two-PE seed text.** Delete the unreachable `PE-MOH`/`PE-CGKIS` dataset definitions entirely; rebuild the STR-DES v2 fixture generator off the live single-PE seed identity. | §1's "deleted rather than aliased" covers the file's text, not only its reachable execution path. **Closed (STR-503/504, commit `4fe369aa`).** |
| 2026-09-03 | **D4 — doc naming/structure.** Mirror NDS/Planning's convention: `02_`/`03_` numbering, standalone gap analysis, separate `FOLLOW_UPS.md`. | Per-repo convention for full-replacement change docs. |
| 2026-09-06 | **D5 — UI route architecture (§10) — resolved: single Desk Page `strategy`.** The three Phase-7 Pages (`strategy-portfolio`, `strategy-plan-workspace`, `strategy-review-task`) and their three bundles were deleted outright (not aliased or redirected; a patch removes the Page records) and replaced by one `kentender_core.desk_page.register("strategy", …)` controller whose Vue root switches three KeepAlive screens on the route. | Phase 1's live trace showed the three-Page split could not satisfy §10's literal path-segment routes (`/app/strategy/plan/{plan_id}/version/{n}/structure`, `/app/strategy/approval/{plan_version_id}`) without a redirect layer, which §17 prohibits. One Page keeps the app mounted across navigations (AGENTS.md §6.1) and gives every screen the same server-returned `action_route` arrays. The Page's `roles` table is empty (KT-STD-001 §3A): the authorization verdict is data returned by the first service call, never a framework 403. |
| 2026-09-06 | **D6 — STR-BR-004 "database-level partial unique index" (§16.1) — MariaDB equivalent.** MariaDB has no partial unique index. The guard is a `SELECT … FOR UPDATE` locking read inside `Strategic Plan Version.validate` (`strategy_domain_guards.assert_no_primary_overlap`), so two concurrent approvals serialise on the competing Active rows and the second fails inside its own transaction. | The guard lives in the doctype controller, not the command layer, so a raw `frappe.get_doc(...).save()` that bypasses `transition_plan_version` is still refused — `TestOverlapGuardBypass.test_overlap_guard_holds_when_the_command_layer_is_bypassed`. |
| 2026-09-06 | **D7 — Strategy Viewer becomes Auditor.** The `Strategy Viewer` DocPerm rows on all five doctypes were replaced by `Auditor` (read/report/export only); the Role itself is hard-deleted by patch. | STR-AC-031 and §6: Auditor is the only non-workflow read responsibility; §3A's Forbidden copy names "Strategy Author, Strategy Approver or Auditor". |
| 2026-09-06 | **D8 — Performance Target period is an ERPNext `Fiscal Year` overlapping the plan period.** Field renamed `financial_year_id` → `fiscal_year` (Link → Fiscal Year); the target's year must overlap the plan period, and the dialog offers only those years plus one "By end of plan period" date option. | §4.5/§12.3; `_Test Fiscal Year` rows on a dev site still appear when they overlap — see FU-03. |

## Headline findings at close

1. **The rebuild's real defects were only visible in a browser.** Static reading and the Python suite were green while the first real journey exposed: an immediate `watch()` referencing later consts (Vue TDZ, "Cannot access before initialization"), SFC `<style scoped>` CSS that esbuild extracts to a file nothing links, string-typed whitelisted floats compared with `<=` (HTTP 500), Escape not closing a dialog once a failed save had disabled the focused button, and a dev server whose dead stdout pipe turned every validation error into a Werkzeug 500. All fixed in this pass; the last is recorded in FU-05.
2. **`strategy_contracts.py` (1,553 lines) and `strategy_permissions.py` are gone.** The four live functions moved into `strategy_consumer.py`; nothing imports the deleted modules (repo-wide grep, gateway contract test green).
3. **No `Strategy Viewer`, `procuring_entity_id`, `pe_fy_context`, `owner_org_unit_id` or `financial_year_id` remains** in metadata, schema, services, seeds, UI or active tests: static scan plus `TestStaticScan.test_live_schema_carries_no_retired_columns` and `test_strategy_viewer_role_is_gone_and_auditor_reads`.

## Carried debts

| Opened | Debt | Status |
|---|---|---|
| Phase 7 | No automated design-fidelity gate against STR-DES-01..10 (`strategy-fidelity.spec.ts`, `make ui-strategy-fidelity-gate`). Rendering, copy and behaviour are proven by `make ui-strategy-gate`; pixel/content fidelity to §11 is not. | Open — FU-01 |
| Phase 4 | Frappe Workspace shortcuts cannot be role-restricted: the "Approval tasks" shortcut on the Strategy Management workspace is visible to every module user; the route it opens (`/app/strategy/my-work`) is itself gated as data. | Open — FU-02 |
| Phase 9 | `kentender_core.tests.test_module_registry` has two failures that predate this pass (`demands` entry / `form/demand` route) and are unrelated to Strategy. | Open — owned by kentender_core |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| STR-G00 | Gap analysis, plan and tracker authored | Done | `02_STR_Rebuild_Gap_Analysis.md`, `03_STR_Rebuild_Implementation_Plan.md`, this document |
| STR-G01 | Repo-wide static scan complete; route-architecture question resolved (D5) | Done | `TestStaticScan` (3 tests) green; D5 resolved in the decision log |
| STR-G02 | Schema matches §4.1/§4.5 exactly; STR-BR-004 rewritten and DB-guarded; clean `bench migrate` | Done | `patches/str_chg_001_v1_7_schema_correction.py` ran clean on `kentender.midas.com` (2026-09-06); `test_live_schema_carries_no_retired_columns`; `TestOverlapGuardBypass` (2 tests) |
| STR-G03 | `resolve_strategy_context()` matches §7/§8 literally; cross-app gateway contract test green | Done | `TestResolveStrategyContext` (3 tests in the v1.7 module + 2 in phase 4); `kentender_procurement…test_gateway_contracts` 3/3 |
| STR-G04 | `Strategy Viewer` role fully removed; D1 recorded as a documented non-action | Done | `patches/str_chg_001_v1_7_delete_strategy_viewer_role.py`; `test_strategy_viewer_role_is_gone_and_auditor_reads`; D1 retained above |
| STR-G05 | `strategy_contracts.py` deleted; dead seed code removed; D2 assignment-ID gap closed | Done | Both modules deleted from the tree; `TestAuditCarriesExercisedAssignment` green |
| STR-G06 | UI route architecture corrected per D5 | Done | One Page `strategy` (`TestOnePageRouteTable`, 2 tests); browser journeys under direct load, reload and back/forward in `tests/ui/smoke/strategy/*.spec.ts` |
| STR-G07 | New artboard set verified against §11; `make ui-strategy-fidelity-gate` passes | In progress | Artboards carry no Procuring Entity text (grep, STR-702); behaviour/copy verified by `make ui-strategy-gate`; fidelity gate not built (FU-01) |
| STR-G08 | §14 seed contract satisfied; KT-STD-001 §8.3/§8.5 updated; idempotent on rerun | Done | KT-STD-001 v1.3 §8.3 lists Esther Muthoni, Dr Alfred Ochieng, Naomi Chebet, Samuel Otieno; `test_str_chg_001_phase5_seed` (2 tests); `TestSeedFailsClosedOnMissingFiscalYear` |
| STR-G09 | All 37 STR-AC IDs evidenced; full module + cross-app + AUTH contract suites green; static scan clean | Done (36 of 37 fully; STR-AC-025 fidelity half open) | `bench --site kentender.midas.com run-tests --app kentender_strategy`: 81 tests OK (2026-09-06); `make ui-strategy-gate`: 7 passed; industry-design gate: 2 passed |

## Work register — Phase 0: gap analysis, plan and tracker

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-001 | Read STR-CHG-001 in full; identify the §1.1 register and §16.1 rules as the primary gap surface | Done | `02_STR_Rebuild_Gap_Analysis.md` §3, §10 |
| STR-002 | Baseline the current implementation against the spec, including commit `ccff1b80` | Done | `02_STR_Rebuild_Gap_Analysis.md` §2, §4–9 |
| STR-003 | Verify the AUTH/STD/CFG mechanisms Strategy depends on | Done | `business_role_registry.py`, `authorization.py`, `site_configuration.py` read against the doc text |
| STR-004 | Survey sibling rebuild docs for precedent | Done | NDS/Planning convention adopted (D4) |
| STR-005 | Resolve D1–D4; record D5 as deferred | Done | Decision log |
| STR-006 | Author the four companion documents | Done | This document and its companions |

## Work register — Phase 1: repo-wide static verification and route-architecture research

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-101 | Repository-wide disposed-concept grep across `kentender_strategy`, `kentender_procurement`, `kentender_budget`, `kentender_core` | Done | Executable scan `TestStaticScan.test_no_retired_concept_in_executable_strategy_code`; cross-app callers re-pointed (`strategy_gateway.py`, `procurement.json` sidebar, `module_registry.py`, `kt_module_registry.js`, `industry-design-gate.spec.ts`) |
| STR-102 | Confirm or refute the STR-BR-004 database-level partial unique index | Done | Refuted for MariaDB → D6 locking-read equivalent |
| STR-103 | Confirm whether `Auditor` is a registered business-role entry or a bare DocPerm role | Done | Registered Site-wide entry in `business_role_registry.py`; now the read role on all five Strategy doctypes (D7) |
| STR-104 | Live route trace of the three-Page split against §10 | Done | Three-Page split could not honour path-segment routes without redirects → D5 |
| STR-105 | Decide the route architecture (D5) | Done | Single Page `strategy` |

## Work register — Phase 2: schema correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-201 | Drop `procuring_entity_id` and `pe_fy_context` from `Strategic Plan` | Done | `strategic_plan.json`; columns dropped by `str_chg_001_v1_7_schema_correction.py` (`ALTER TABLE … DROP COLUMN`); `test_live_schema_carries_no_retired_columns` |
| STR-202 | Drop `owner_org_unit_id` from `Strategic Plan` | Done | Same patch and test |
| STR-203 | Rename `financial_year_id` → `fiscal_year` on `Performance Target` | Done | `performance_target.json`; patch copies values then drops the old column; `cu_305_repoint_performance_target_fiscal_year.py` guarded with `has_column` |
| STR-204 | Rewrite `_assert_no_primary_overlap()` with no PE/OU qualifier | Done | `strategy_domain_guards.assert_no_primary_overlap`; `test_str_chg_001_phase2_lifecycle.test_activate_rejects_overlapping_primary_plan`; `TestOverlapGuardBypass.test_non_overlapping_primary_plans_may_both_be_active` |
| STR-205 | Build the DB-level guard | Done | D6; `test_overlap_guard_holds_when_the_command_layer_is_bypassed` |
| STR-206 | Migration patch for the field drops + rename | Done | `patches.txt` post_model_sync; `bench migrate` clean on the dev site |

## Work register — Phase 3: service and command contract correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-301 | Rebuild `resolve_strategy_context()` to the literal §7/§8 shape | Done | `strategy_consumer.resolve_strategy_context(*, as_of_date, fiscal_year, include_supporting)`; `TestResolveStrategyContext` (3): exactly-one-input rule, typed `STRATEGY_CONTEXT_NOT_FOUND`/`STRATEGY_CONTEXT_AMBIGUOUS`, no PE/OU keys, supporting frameworks only on request in title order |
| STR-302 | Update `api/strategy_consumer_api.py`; drop the `procuring_entity` transport kwarg | Done | Wrapper takes `as_of_date, fiscal_year, include_supporting` only |
| STR-303 | Verify `strategy_gateway.py` + `test_gateway_contracts.py` | Done | Gateway calls `resolve_strategy_context(as_of_date=today)`; 3/3 green; Planning's `list_eligible_strategic_objectives()` returned both seeded objectives in `bench console` |
| STR-304 | Generated references accepted everywhere a record ID is | Done | `strategy_reference.resolve_plan_name/resolve_version_name`; `TestPortfolioAndReferences.test_read_contracts_accept_generated_references` |
| STR-305 | Whitelisted numeric input coerced before range validation | Done | `strategy_domain_guards` coerces `target_value` with `float()` ("Target Value must be a number"); browser target save no longer 500s |

## Work register — Phase 4: roles and permission cleanup

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-401 | Remove `Strategy Viewer` DocPerm rows from all 5 doctype JSONs + Page/Workspace JSONs | Done | All five doctype JSONs carry `Auditor` read/report/export instead; `strategy_management.json` workspace carries no Viewer role |
| STR-402 | Remove `ROLE_VIEWER`/`UNRESTRICTED_READ_ROLES` references | Done | `strategy_permissions.py` deleted; `strategy_ui_contracts.py` rewritten |
| STR-403 | Patch hard-deleting the `Strategy Viewer` Role | Done | `patches/str_chg_001_v1_7_delete_strategy_viewer_role.py` (Has Role, DocPerm, Custom DocPerm, Role) |
| STR-404 | Clean any remaining `Strategy Viewer` seed pairing in `kentender_core` | Done | `site_setup.py` grants Esther (Author), Alfred (Approver), Naomi (Auditor); no Viewer grant |
| STR-405 | Record D1 as a documented non-action | Done | Decision log |
| STR-406 | Approval-task access denied as data, never as a permission modal | Done | `get_version_review_overview` returns `{"forbidden": True, "reason": "approver_required"}`; `test_approval_task_is_denied_as_data_without_an_approver_assignment`; browser: `strategy-access.spec.ts` (auditor) and `strategy-approver.spec.ts` (submitting author) |

## Work register — Phase 5: dead code removal

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-501 | Extract the live functions out of `strategy_contracts.py` into `strategy_consumer.py` | Done | `validate_strategy_reference`, `build_strategy_reference`, `list_active_targets`, `_node_ancestor_path` in `strategy_consumer.py`; phase 4/6 tests import from there |
| STR-502 | Delete `strategy_contracts.py` wholesale | Done | Deleted with `strategy_permissions.py`; suite green |
| STR-503 | Delete dead two-PE dataset text in `kentender_mvp_v1_strategy.py` (D3) | Done | Commit `4fe369aa`; `test_legacy_kisumu_world_is_absent` |
| STR-504 | Rebuild `seed_str_des_v2_fixture()`/teardown off the single-PE seed | Done | Used by `seeds/playwright_ui_fixtures.reset_submitted_fixture` for the approver journey |
| STR-505 | Thread the exercised assignment ID into audit events (D2) | Done | `strategy_audit.record_event(business_role=, assignment=)`; `require_plan_create_capability` returns the decision's assignment; `TestAuditCarriesExercisedAssignment.test_submit_event_records_business_role_and_assignment_id` |
| STR-506 | Fix the stale `v1.5 §7` citation in `business_role_registry.py` | Done | Now `STR-CHG-001 v1.7 §6` |

## Work register — Phase 6: UI route architecture correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-601 | Execute D5: one Page, three screens, §10 routes | Done | `page/strategy/strategy.json` (roles empty), `public/js/strategy_page.js` (`desk_page.register`), `strategy/Strategy.vue` + `screens/{PortfolioScreen,PlanWorkspaceScreen,ApprovalTaskScreen}.vue`; legacy Pages, bundles and Playwright specs deleted; `patches/str_chg_001_v1_7_delete_legacy_strategy_pages.py` |
| STR-602 | Browser journey proving direct-load/refresh/back-forward for all canonical routes | Done | `strategy-author.spec.ts` (reload on `/version/2/structure`, back/forward across tabs), `strategy-approver.spec.ts` (reload on `/approval/…/history`, back/forward), `strategy-access.spec.ts` (direct load of all three routes as an unassigned actor) |
| STR-603 | Portfolio filters server-side; counts and rows share one predicate | Done | `get_strategy_portfolio(search, plan_role, status)`; `test_portfolio_filters_are_server_side_and_counts_match_rows`; browser: status filter + no-match + clear |
| STR-604 | User-correctable errors inline, never a Frappe modal (AGENTS.md §6.10 / §3A) | Done | Per-field errors on the new-plan form, duplicate-FY target refusal inside the dialog, "Not ready for submission" inline; every spec asserts `expectNoFrappeModal` |
| STR-605 | Forbidden panel per KT-STD-001 §3A on all three screens | Done | `strategy-access.spec.ts` "an actor with no Strategy assignment lands on the inline Forbidden state everywhere" |

## Work register — Phase 7: artboard / design-fidelity verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-701 | Verify STR-DES-01..10/Shell/index artboards against §11 exact content | In progress | Copy and structure ported by hand while building the screens; no automated fidelity check (FU-01) |
| STR-702 | Resolve the CU-3xx "9 of 20 artboards depict PE dimension" note against the new artboard set | Done | `grep -l "Procuring Entity" strategy_design/*.dc.html` → no hits |
| STR-703 | Build `strategy-fidelity.spec.ts` + `make ui-strategy-fidelity-gate` | Planned | FU-01 |
| STR-704 | Audit the legacy `ui-strategy-*-gate` Makefile targets | Done | Three stale targets replaced by `make ui-strategy-gate` (`npm run test:ui:smoke:strategy`); `tests/ui/smoke/strategy-alignment/` and the four `loginAsStrategy*` helpers deleted |

## Work register — Phase 8: seed contract alignment

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-801 | Add the Strategy actors + fixture timeline to KT-STD-001 §8.3/§8.5 | Done | KT-STD-001 v1.3 §8.3 rows for Esther Muthoni, Dr Alfred Ochieng, Naomi Chebet, Samuel Otieno (expired) |
| STR-802 | Build the exact §14.3 MOH plan seed | Done | `seeds/kentender_mvp_v1_strategy.py` drives the governed commands as Esther/Alfred; live site holds `MOH-SP-0007` / `MOH-SPV-0007` Active; `test_the_seed_builds_the_real_moh_plan_and_is_idempotent` |
| STR-803 | Verify the §14.2 fail-closed Fiscal Year check | Done | `TestSeedFailsClosedOnMissingFiscalYear.test_missing_fiscal_year_aborts_before_any_write` |
| STR-804 | Verify the rebuilt V2 fixture matches §14.4 | Done | Approver journey sees Version 2 "Submitted for approval" by Esther Muthoni with the single change "At least 80 → At least 85" on the FY 2027-2028 target |
| STR-805 | Browser fixtures: `seeds/playwright_ui_fixtures.py` (`ensure_actors`, `reset_default`, `reset_submitted_fixture`, `reset_draft_fixture`) | Done | Each spec resets in `beforeAll` and purges in `afterAll`; the site ends at the §14 baseline |

## Work register — Phase 9: acceptance-contract mapping and release verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-901 | Map all 37 STR-AC IDs to tests/evidence | Done | Table below |
| STR-902 | Full `kentender_strategy` suite green | Done | `bench --site kentender.midas.com run-tests --app kentender_strategy` — 81 tests across the runner's two batches, OK (2026-09-06, final run after the STR-AC-033 sweep) |
| STR-903 | Cross-app contract suite (Budget + Procurement) green | Done | `kentender_procurement.procurement_planning.tests.test_gateway_contracts` 3/3; Budget consumer functions covered by `test_str_chg_001_phase6_consumers.test_budget_consumer_functions_work_against_the_fixture` |
| STR-904 | AUTH contract: no Strategy path reintroduces a User Permission read | Done | `test_str_chg_001_phase3_governance` (5 tests); `test_administrator_without_assignment_has_no_workflow_capability` |
| STR-905 | Re-run the static scan; confirm clean | Done | `TestStaticScan` 3/3 |
| STR-906 | Browser gate | Done | `make ui-strategy-gate` — 7 passed (author ×2, approver ×2, access ×3), zero page console errors; `industry-design-gate.spec.ts` 2 passed on `/desk/strategy` |
| STR-907 | Manual end-to-end walk-through on the seed world (Playwright MCP, 2026-09-06) | Done | Esther: portfolio → View → successor → target 80→85, new objective/indicator/target, duplicate-FY and >100% refused inline, reload, submit, readiness 4×Ready, history. Alfred: My work → four approval tabs → Return with reason → Esther resubmits → Approve → V2 Active / V1 Superseded. Naomi read-only; Samuel Forbidden on all three routes; Administrator technical read. New plan `MOH-SP-0008` registered with generated references (purged afterwards) |

## Acceptance-criteria mapping (§15)

| ID | Criterion (condensed) | Status | Evidence |
|---|---|---|---|
| STR-AC-001 | Installs/imports without legacy Demands package or Procurement Home | Done | App imports across the full suite; no `demands` import anywhere in `kentender_strategy` |
| STR-AC-002 | No executable metadata/route/service/field/label/seed/test refers to disposed concepts | Done | `TestStaticScan.test_no_retired_concept_in_executable_strategy_code` (tokens incl. Strategic Outcome, Value Commitment) |
| STR-AC-003 | Author creates a Draft plan, receives generated references | Done | `strategy-author.spec.ts` "creates a brand-new Draft plan…" (`MOH-SP-\d{4}` eyebrow); `test_plan_gets_generated_id_and_rejects_client_edit` |
| STR-AC-004 | No Active assignment (incl. Administrator/System Manager) cannot create/submit/return/approve | Done | `test_unassigned_user_denied_stc_ac_004`, `test_administrator_without_assignment_has_no_workflow_capability`; browser: Administrator sees no business action |
| STR-AC-005 | Hierarchy Pillar→Programme→optional Sub-programme→Objective; Indicator under Objective; Target under Indicator | Done | Phase 1 domain-model tests; browser adds Objective → Indicator → Target under the seeded Sub-programme |
| STR-AC-006 | Objective and Indicator distinct; no Strategic Outcome | Done | `test_indicator_must_measure_objective`; static scan token "Strategic Outcome" |
| STR-AC-007 | Target validation: period, comparison, unit-compatible value, percentage range | Done | `test_target_requires_exactly_one_period_anchor`, `test_invalid_comparison_rejected`, `test_percentage_target_value_out_of_range_rejected`, `TestTargetPeriodRule` (2) |
| STR-AC-008 | Readiness blocks submission | Done | `test_submit_blocked_when_not_ready`; browser: "Not ready for submission" inline on the new plan |
| STR-AC-009 | Plan Item selects exactly one Objective | Done | `test_list_strategy_objectives_only_from_active_version_with_path`, `test_snapshot_rejects_wrong_node_type`; Planning gateway 3/3 |
| STR-AC-010 | Only Author/Approver are workflow responsibilities; no self-approval | Done | `test_author_cannot_return_or_approve_own_version_even_with_approver_role`, `test_dual_role_actor_may_approve_a_version_someone_else_submitted` |
| STR-AC-011 | Return requires reason; full history preserved | Done | `test_return_reason_length_enforced`; browser: Return with reason, history names Dr Alfred Ochieng and the reason |
| STR-AC-012 | Submitted/Active/Superseded immutable; correction via successor | Done | `test_structure_edit_rejected_on_active_version`; browser: Active structure read-only, successor editable |
| STR-AC-013 | Concurrent approval cannot create overlap, guard holds when bypassing the command layer | Done | `TestOverlapGuardBypass` (2) — D6 |
| STR-AC-014 | Successor approval atomically activates + supersedes | Done | `test_activate_supersedes_previous_active_version_of_same_plan`; browser: V2 Active, V1 Superseded after one Approve |
| STR-AC-015 | Zero/multiple matches → typed errors, never chosen by preference | Done | `test_exactly_one_input_and_typed_zero_and_ambiguous_errors`, phase 4 `TestResolveStrategyContext` (2) |
| STR-AC-016 | `resolve_strategy_context` correct for date or Fiscal Year, no PE/OU input | Done | `test_fiscal_year_input_returns_the_covering_active_primary_and_no_scope_keys`; gateway contract test asserts the parameter set |
| STR-AC-017 | `list_strategy_objectives` only Active Objectives with IDs + ancestor paths | Done | `test_list_strategy_objectives_only_from_active_version_with_path` |
| STR-AC-018 | `get_strategy_lineage` exact IDs/types/titles in order | Done | `test_get_strategy_lineage_for_node_indicator_and_target`, `test_get_strategy_lineage_resolves_the_fixture_objective` |
| STR-AC-019 | Snapshot captures exact lineage, immutable and idempotent | Done | `TestCreateStrategySnapshot` (3) |
| STR-AC-020 | Downstream direct-table mutation and Draft reads rejected | Done | `test_snapshot_rejects_non_active_version`, `test_validate_and_build_strategy_reference_against_active_version`, `test_structure_edit_rejected_on_active_version` |
| STR-AC-021 | Read access ≠ approval-task access | Done | `test_approval_task_is_denied_as_data_without_an_approver_assignment`; browser: auditor Forbidden on `/approval/…` |
| STR-AC-022 | Counts/rows/routes/APIs share one predicate; hidden plan unreachable by route | Done | `test_portfolio_filters_are_server_side_and_counts_match_rows`; `get_plan_workspace` returns Forbidden as data for an unassigned actor (`strategy-access.spec.ts`) |
| STR-AC-023 | Default seed deterministic; second run no-op | Done | `test_the_seed_builds_the_real_moh_plan_and_is_idempotent`, `test_seed_idempotent_and_produces_real_active_data` |
| STR-AC-024 | Missing Fiscal Year fails seed, no fallback | Done | `TestSeedFailsClosedOnMissingFiscalYear` |
| STR-AC-025 | Four routes render without console error and match approved designs | In progress | Render/console: `make ui-strategy-gate` (every test asserts an empty console-error list) and industry-design gate. Design fidelity: FU-01 |
| STR-AC-026 | Loading/no-match/forbidden/server-error states disclose nothing false or unauthorised | Done | `strategy-access.spec.ts` asserts no rows, tabs, search or count painted with the Forbidden panel; no-match state in the author spec |
| STR-AC-027 | Frappe header/breadcrumb reused; no PE/scope/context selector | Done | Screens render inside `kentender_core.desk_page`; no selector component exists in `public/js/strategy/` |
| STR-AC-028 | No page/API accepts VC/source-ref/evidence/attachment/contact/baseline/treatment/actual/corrective data | Done | Static scan; write payload limited to `PLAN_IDENTITY_FIELDS` / `VERSION_FIELDS` / node, indicator and target fields |
| STR-AC-029 | Approver inspects the exact submitted version on all four tabs | Done | `strategy-approver.spec.ts`: Overview, Structure ("At least 85"), Changes ("Changes from Active Version 1"), History — all for Version 2 |
| STR-AC-030 | Return/Approve on every tab; stale version/status rejected | Done | Decision footer visible on every tab and after reload; `test_stale_write_rejected`; UI passes `expected_version` |
| STR-AC-031 | No reference to retired roles or statuses | Done | Static scan; `test_strategy_viewer_role_is_gone_and_auditor_reads` |
| STR-AC-032 | Every write authorised through Active URA; no User Permission/capability/scope path | Done | `strategy_authorization.py` uses `authorise_record` only; phase 3 governance tests; audit events carry the exercised assignment |
| STR-AC-033 | No `procuring_entity`/`procuring_entity_id`/`owner_org_unit_id`/`FinancialYear` reference | Done | Static scan (bare `procuring_entity` is a scanned token) + live schema test; `test_portfolio_carries_no_entity_dimension`; the accepted-and-ignored entity kwargs, the dead `pe_slug` helper and the unrendered portfolio entity banner were removed on 2026-09-06 |
| STR-AC-034 | Author/Approver registered Site-wide; no OU scope check | Done | `test_roles_exist_and_registry_binds_them_site_wide`; every `authorise_record` call passes `organisation_unit=""` |
| STR-AC-035 | Verdict resolved before render; denied actor sees the inline panel with nothing else painted; no modal on load | Done | Page `roles` empty; `strategy-access.spec.ts` (all three routes) |
| STR-AC-036 | Panel names the responsibilities and a KenTender administrator; no line manager | Done | Copy asserted in `strategy-access.spec.ts` |
| STR-AC-037 | Selecting the module without access pushes its route, highlights it, lands on Forbidden; never hidden | Done | `strategy-access.spec.ts` asserts the URL and the visible sidebar link |

## Verification record (2026-09-06)

| Check | Command | Result |
|---|---|---|
| Strategy Python suite | `bench --site kentender.midas.com run-tests --app kentender_strategy` | 81 tests, OK |
| Planning gateway contract | `… --app kentender_procurement --module kentender_procurement.procurement_planning.tests.test_gateway_contracts` | 3 OK |
| Core module registry | `… --app kentender_core --module kentender_core.tests.test_module_registry` | 9 OK, 2 pre-existing failures (`demands`) unrelated to Strategy |
| Browser gate | `make ui-strategy-gate` | 7 passed |
| Industry design gate | `npx playwright test tests/ui/smoke/industry-design/industry-design-gate.spec.ts` | 2 passed |
| Migration | `bench --site kentender.midas.com migrate` | three v1.7 patches applied cleanly |
| Not run | full `kentender_budget` / `kentender_procurement` suites | out of this pass's scope; the only Strategy-facing consumers are covered by the gateway and phase 6 tests |

## §14 seed-contract cross-reference

PLN-CHG-001 v1.13 and BUD-CHG-001 consume `list_strategy_objectives`/`create_strategy_snapshot` and the Strategy reference builders with no PE/OU argument. Planning's `strategy_gateway.py` was re-pointed in this pass (STR-303); Budget's consumer calls are exercised by `test_str_chg_001_phase6_consumers`. SEED-001 v1.0 §3.4 is the seed of record for the MOH plan.
