# Audit remediation: handover (7 October 2026, end of the Wave 4R work)

Start here in a fresh session. Read `AGENTS.md` and `CLAUDE.md` first. Repository `/home/midasuser/frappe-bench/apps/kentender_v1`, branch `mvp1/dev`, bench `/home/midasuser/frappe-bench`, dev site `kentender.midas.com`, test site `kentender-test.local` (port 8001). Plain English; no new product code is started by this file.

## 1. State in numbers

279 tracked rows (237 audit findings + 42 regression findings RG-01..RG-42). From `REMEDIATION_TRACKER.md`, counted from the rows:

| Wave | Findings | Todo | Red | Green | Verified | Blocked |
|---|---|---|---|---|---|---|
| 1 Doors anyone can open | 25 | 0 | 2 | 8 | 14 | 1 |
| 2 REST bypass | 11 | 0 | 1 | 2 | 8 | 0 |
| 3 Money | 28 | 0 | 2 | 5 | 20 | 1 |
| 4 Segregation | 39 | 0 | 0 | 11 | 24 | 4 |
| 4R Regression findings | 42 | 1 | 0 | 36 | 0 | 5 |
| 5 Dead-end flows | 37 | 36 | 0 | 1 | 0 | 0 |
| 6 Audit trail, hazards | 14 | 13 | 0 | 1 | 0 | 0 |
| 7 Medium/Low and documents | 83 | 83 | 0 | 0 | 0 | 0 |
| **All** | **279** | **133** | **5** | **64** | **66** | **11** |

Severity: Critical 3 (2 Verified, 1 Green); High 38 (23 V, 8 G, 1 Blocked, 6 Todo); Medium 129 (35 V, 31 G, 2 Red, 3 B, 58 T); Low 109 (6 V, 24 G, 3 Red, 7 B, 69 T). Red rows: XC-020, XC-021, XC-129, XC-133, XC-136. Wave 4R open: RG-33 (not done); RG-28, RG-35, RG-37, RG-38, RG-39 (owner decisions).

Owner decisions of 7 October are built: D5 (Head of Procurement Function publishes the Annual Plan, RG-01), D6 (legacy Tender Configurations retired completely, RG-04/RG-05, XC-143, XC-011), D7 (evaluation separation, RG-15, AWD-001). D1 to D4 earlier.

Git: 117 commits on `mvp1/dev` are local and unpushed (`git log --oneline origin/mvp1/dev..HEAD | wc -l`; 116 before the wind-up commit). 94 `.png` files show as modified under `docs/`; never stage them.

## 2. Done, verified, not done

- **Done (code, Green):** Waves 1 to 4 as recorded, plus 36 Wave 4R rows. Evidence: Python module tests on the test site and one vitest file.
- **Verified (66 rows):** only the rows the 7 October regression sweeps judged CLOSED and whose tests passed in integration gate 1. Wave 4R fixes are Green, not Verified.
- **Not done, stated plainly:** no pre-wave baseline was ever run; the final read-only regression re-check of the Wave 4R fixes has not run; INT-D (procurement suite, second gate) is incomplete (55 of 273 modules; blocked by orphan row `Annual Plan Version PLN-MOH-2101-001-V1`; 10 modules errored at setUp from that residue; resume at `bid_evaluation.tests.test_evl_intake`, about 218 modules left); nothing was seen in a browser; nothing has been run on the dev site (no migrate, patch, seed, asset build); Waves 5 to 7 (134 rows) and the document changes are not started. INT-C (156 modules of core, budget, strategy, suppliers) is complete: R 0, E 129 first-pass failures, D 0.

## 3. Restart the machine's services after a reboot

All from `/home/midasuser/frappe-bench`, stdin closed, output redirected (a server whose output pipe dies turns every error into a fake 500). Redis cache is port 13000, queue 11000.

```
cd /home/midasuser/frappe-bench
nohup redis-server config/redis_cache.conf > logs/redis_cache.out 2>&1 < /dev/null &
nohup redis-server config/redis_queue.conf > logs/redis_queue.out 2>&1 < /dev/null &
nohup bench serve --port 8000 > logs/bench-serve.log 2>&1 < /dev/null &
nohup bench worker > logs/worker.log 2> logs/worker.error.log < /dev/null &
apps/kentender_v1/scripts/test-site.sh serve        # test site on :8001; it already uses nohup and closed stdin
apps/kentender_v1/scripts/test-site.sh status       # server up? canonical world intact?
```

Check: `redis-cli -p 13000 ping`, `redis-cli -p 11000 ping`, `curl -s http://127.0.0.1:8000/api/method/ping`, and `make ui-queue-check` from `apps/kentender_v1/` (an undrained background-job queue breaks fixture resets and shows up as a misleading `NameError`; `FIX=1` drains it). A killed test process can leave the test site with orphan rows and held locks; a machine restart killed INT-C and INT-D once already.

## 4. Test-site procedure

Tests write real rows with no rollback: run them only on `kentender-test.local`, one module per call, always under the lock:

```
cd /home/midasuser/frappe-bench
flock /tmp/kt-test-site.lock bench --site kentender-test.local run-tests --app <app> --module <dotted.module>
```

Rebuild (copies the dev database and files over the test site; the code is the shared checkout, so **rebuild only with everything committed**, because a rebuild plus developer-mode migrate can undo uncommitted DocType JSON edits):

```
cd /home/midasuser/frappe-bench
flock /tmp/kt-test-site.lock apps/kentender_v1/scripts/test-site.sh rebuild --yes      # same as: make test-site-rebuild from apps/kentender_v1/
flock /tmp/kt-test-site.lock bench --site kentender-test.local migrate                 # needed: the copy is dev's UNMIGRATED schema
bench --site kentender-test.local clear-cache
```

The rebuild script does not migrate (it assumes dev is already migrated). Dev is not migrated yet, so migrate the test site after every rebuild; that runs the two drop patches against empty retired tables and the new schema, and it can rewrite tracked files (`workspace_sidebar/*.json` timestamps): check `git status` and do not commit those by accident. After the migrate, validate the canonical world through a Frappe context, because `bench execute kentender_core.seeds.canonical.validate` can print only `NameError` and hide the real exception:

```
cd /home/midasuser/frappe-bench/sites && ../env/bin/python - <<'EOF'
import frappe
frappe.init(site="kentender-test.local", sites_path=".")
frappe.connect()
from kentender_core.seeds import canonical
print(canonical.validate(current="award", next_year="annual_plan"))   # expect ok: true
frappe.destroy()
EOF
```

Run browser tests only through `apps/kentender_v1/scripts/test-site.sh run npx playwright test <spec> --workers=1`, one run at a time. Strategy tests need the ERPNext `_Test Fiscal Year 2040..2050` rows absent (delete them on the test site if a Strategy module errors with a fiscal-year overlap). A canonical-dependent run needs a fresh rebuild; the full suite leaves the canonical world invalid.

## 5. Next steps, in order

1. Rebuild the test site (section 4) with everything committed; validate the canonical world; `make ui-queue-check`.
2. Resume INT-D from `kentender_procurement.bid_evaluation.tests.test_evl_intake` (273 modules in all; modules before it were OK except as listed in `progress/INT-D.md`), one module per call under the lock, canonical validate every few modules; re-run the ten setUp-error modules named in the tracker section. Classify failures R, E or D from evidence; record in `progress/INT-D.md`.
3. Final read-only regression re-check of the Wave 4R fixes with the four sweeps (authorization, sod, state-machine, money-concurrency), reading code and tests, no writes. Output next to `regress-*.md`.
4. Reconcile the tracker: Green to Verified only where the re-check says CLOSED and the module tests pass; re-open anything not closed. Recount the dashboard from the rows.
5. Owner runs the dev-site actions in `REMEDIATION_DEV_ACTIONS.md` (backup, pre-checks, migrate, asset builds, restart then clear-cache, post-checks). Dev may already be failing Planning and Budget paths until the migrate runs (the code is live before the schema).
6. Browser checks in `REMEDIATION_BROWSER_CHECKS.md`, test site first, then dev.
7. A document-change protocol session using `DOC_CHANGE_REQUESTS.md` as input (skill `anthropic-skills:kentender-document-change`): full-replacement next versions, registry, cross-references, Proposed status until the owner approves.
8. Waves 5 to 7 only on the owner's go-ahead (Wave 5 first: XC-121 and PLN-020 sit next to RG-01).

## 6. Pending owner decisions (options and defaults in `REMEDIATION_FOLLOW_UPS.md`, part A)

1. 18-digit storage and the 12-digit ceiling (XC-129, RG-28); KES scale 2 as a site constant or currency-driven (XC-133, RG-28); the 15-digit float deviation in BUD.
2. Technical principals on commands, `sod_tags` consumers, later System Manager grants (XC-136, RG-39).
3. Technical Operator redelivery as "correspondence" (RG-37); addendum maker-checker (RG-38).
4. Do TM2 and Tender Configurations mentions in `docs/`, `archive/` and the sidebar label count against D1 and D6 (RG-35)?
5. Guest supplier registration (XC-020, RG-12): retire, or build the verification step; the `prepare_registration` role list; real supplier-registry responsibilities; an approved KTSM document (DCR-14); retire the Reference Data Manager surface.
6. Mandatory idempotency key on Budget governance commands (RG-16).
7. One person holding both Head of Procurement and Accounting Officer (Q3); AWD-003 external-order evidence; committed amounts on a corrected award.
8. Secretary declaration and secretary write commands (EVL-016).
9. Late final channel confirmation exit and the "Lapsed" addendum status (TND-002, Q6); the meaning of "prepared" for Tender segregation; Opening `processing_actors`.
10. Strategy "author" (STR-006); withdraw-for-correction and `CancelPlanUpdate` in the plan segregation chain (PLN-021, XC-134); rounding of the required reservation (XC-132); whether the Head who signed a plan may also publish it; technical-operator "Your turn" wording (PLN-020).
11. Requisition certification readings (RG-14 follow-ups), requisition draft read scope (REQ-007).
12. NDS wire contract (keep v2 or v3), Plan Entry quantity precision 3, unknown-field code.
13. Retire the legacy surfaces: `procurement_lifecycle` layer, old `procurement_home` page and the Journey list (RG-33), Civic Ledger library, empty `STD *` tables, orphan v1 child doctypes.
14. Destructive-patch guard default; Strategy snapshot as HTTP contract or in-process; Departmental Plan unique (unit, year).
15. BUD items: Close with an open successor, funding source on the requisition projection (BUD-BR-008), CurrencyBasis stored on the Budget root, stamp on successor creation.
16. Test policy: tests that assume an empty site against the canonical world (INT-B 2).

## 7. Known accepted environmental failures (class E; not regressions)

Evidence is in `progress/INT-A.md`, `INT-B.md`, `INT-C.md`. Do not chase these again without new evidence.

- **Core (37 tests in 21 modules):** `test_backfill_pe_fy_context_links` (4), `test_business_action`, `test_exception_record`, `test_master_data`, `test_typed_attachment`, `test_wave0_smoke`, `test_workflow_guard` (Procuring Entity without `reporting_currency`); `test_canonical_seed` (3: `test_a_reservation_stamped_requisitions_ns_is_not_a_stray`, `test_a_second_full_run_changes_nothing`, `test_procurement_rules_are_fixture_verified`; residue); `test_dem_seed_004_orchestrator_demands`; `test_industry_design_gate`, `test_industry_design_scope`; `test_kentender_mvp_v1_seed_contract` (setUpClass); `test_kt_cl_shell_layout_guard` (3); `test_module_registry` (2); `test_stitch_desk_chrome_gate` (2); `test_portal_runtime`; `test_procurement_settings::test_a_schedule_nobody_uses_and_that_has_not_started_is_corrected_in_place`; `test_reference_data_seed_mvp1` (3); `test_seed_v1`; `test_stable_platform_seed` (3); `test_technical_read_conformance` (3 errors, 1 failure); `test_artboard_provenance_gate` (load error while Strategy year 2040-2041 exists).
- **Procurement (INT-B, 44 tests):** E-1 `bid_evaluation.tests.test_evl_intake::test_a_final_no_bids_opening_closes_the_preparation`; E-2 `bid_submission.tests.test_acceptance_gaps::test_every_action_a_read_emits_has_exactly_one_mapping`; E-3 `departmental_needs.tests.test_departmental_needs_architecture` (2); E-4 `test_departmental_needs_lifecycle::test_selectable_years_and_workspace_filtering_span_two_fiscal_years`; E-5 `test_departmental_needs_seed::test_the_cleared_variant_supplies_no_plan_references`; E-6 `departmental_needs.tests.test_home_provider` (3, acting Head's assignment expired); E-7 `procurement_lifecycle` (`test_r3_014_current_stage_calculator` 2, `test_r3_019_permission_filtering` 3, `test_r4_013_technical_evidence_drawer`, `test_r5_002_procurement_journeys_for_strategy_node` 3); E-8 `procurement_planning.tests.test_dead_end_matrix`; E-9 `procurement_requisitions` `test_draft_commands`, `test_read`, `test_ovs_requisition_reads` (one each); E-10 `setup.tests` `test_g0_015_cross_app_workspace_boot`, `test_procurement_home_page_roles`, `test_procurement_sidebar_g0_012_contract` (2); E-11 `tenders.tests.test_read` (3). E-12 (`tender_configurations`) no longer exists.
- **Also seen, not caused by this work:** Planning `test_analytics_provider::test_a_departmental_author_gets_departmental_plans_only_and_no_plan_items`, `test_home_provider::test_an_accepted_plan_missing_a_later_need_asks_the_department_to_update_it`; `award.tests.test_awd_decision::test_no_award_follow_up` (leaked `bud.*` HOPF users); `test_evl_meetings::test_a_reader_with_no_responsibility_and_no_row_gets_the_forbidden_verdict_and_a_department_head_does_not`; `test_ui01_layout_css_contract` and `test_workflow_guard` set-up errors on the shared test site.

## 8. Never do

- Write to the dev site from an agent session: no migrate, patch, seed, cache clear, SQL, test run or Playwright run on `kentender.midas.com` without the owner's say. State any change that adds a migrate, patch or seed before it lands (code is live on dev at once).
- Run any Python or browser test outside `flock /tmp/kt-test-site.lock` and the test site; run two Playwright runs at once (a VS Code Playwright run may be mutating the test site unannounced; `make ui-queue-check` first).
- Rebuild the test site with uncommitted edits.
- `git add -A`, stage `.png` files, or commit without explicit paths (`git add <exact files>` then `git commit -- <exact files>`); another session shares the index and may stage or delete files.
- Use plain `bench build` or an app-level Yarn build (use `./scripts/bench-with-node.sh build --app <app>`).
- Set `kt_allow_destructive_patches` to get past a refusal; reset passwords or force-logout on a live site; edit anything under `docs/mvp-1-r1` outside the document-change protocol; mark a document Approved without the owner.
- Delete orphan test rows by raw SQL unprompted (the permission classifier refused it once); rebuild the test site instead.
- Claim Verified for a Wave 4R row, or "browser tested" for anything, before it was actually observed.

## 9. Where things are

`audit/REMEDIATION_TRACKER.md` (rows, decisions D1 to D7, dashboard, gate sections); `audit/FINDINGS.md` (the 237 findings); `audit/regress-*.md` (the four regression sweeps); `audit/progress/*.md` (one file per work package); `audit/REMEDIATION_FOLLOW_UPS.md`, `REMEDIATION_DEV_ACTIONS.md`, `REMEDIATION_BROWSER_CHECKS.md`, `REMEDIATION_DOC_FOLLOW_UPS.md`, `DOC_CHANGE_REQUESTS.md` (consolidated, regenerated by hand); `audit/tm2-inventory.md`, `audit/tc-inventory.md` (retirement inventories). Memory notes worth reading first: `frappe-queue-overload-masked-trap`, `separate-test-site-2026-10-01`, `audit-remediation-decisions-2026-10-06`, `frappe-run-tests-no-rollback`, `feedback-shared-test-worlds`, `concurrent-session-shared-index`.
