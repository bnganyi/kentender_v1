# PLN-CHG-001 v1.12 — Procurement Planning correction — tracker

**Authority:** `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_12.md` (approved 3 September 2026).
**Companions:** `02_PLN_Rebuild_Gap_Analysis.md`, `03_PLN_Rebuild_Implementation_Plan.md` (decision register D1–D15, owner defaults O1–O6, phase design, execution rules).
**Supersedes-in-tracking:** the v1.2 cycle (closed 31 August 2026, archived as `IMPLEMENTATION_TRACKER_v1_2_closed.md`, 136 Python + 69 vitest + 29 Playwright green in its final state). That work is the baseline this cycle corrects; its 32 headline findings remain valid.
**Status:** Phases 0–1 closed 5 September 2026. Phase 2 In progress.
**Started:** 5 September 2026.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. A row touching a file that still references a spec-prohibited concept is not `Done`. Prohibited here: `pe_fy_context`, `procuring_entity` (any Planning field, argument or fixture), KenTender `Financial Year` / `Unit Of Measure` links, `User Permission` as authority, `Departmental Plan Submission Window`, `Plan Reservation Reference` / `Funding Reservation` / any reservation call, per-item Finance tasks, `Budget Officer` as the Finance actor, `Planning Auditor`, a stored `Pending addition`, a typed actual date, Stitch markup, `kt_cl_surface_registry.js` entries, sidebar work-queue entries, browser context as authority.
4. Deletion lands in the same phase as its replacement.
5. Screens are built from the `.dc.html` artboard's markup class-for-class; behaviour from §12, never from artboard content. Reusing a component for a screen whose artboard changed means re-porting it.
6. Slice gates (PLN-G03..G06) close only on: component tests, a design-fidelity spec per artboard, a Playwright spec on the D13 world with per-role logins (each §6 actor served plus one out-of-scope actor), absence assertions on refusal paths, first paint **and** one interactive re-render observed live, zero page-specific console errors.
7. Static and architecture guards are `Done` only when proven by a planted violation.
8. Fixture instants are pinned, never `now`-relative; the Python suite and Playwright never run concurrently on the site (they each move the DPP flag).
9. Diagnosis follows the KT-STD-001 §5 ladder; a full-suite run is never the first diagnostic step. A phase overrunning its target by half stops and records why.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-05 | D1–D15 as recorded in `03_PLN_Rebuild_Implementation_Plan.md` §2. | See plan. |
| 2026-09-05 | O1–O6 owner defaults applied without pause (execution rule 1). | Owner instruction 5 Sep 2026. |
| 2026-09-05 | v1.2 companion docs archived under `*_v1_2*` names rather than overwritten. | Their findings and evidence stay citable. |

## Headline findings (read before touching code)

1. Planning never adopted the AUTH resolver: `services/authority.py` is `frappe.get_roles` + `User Permission`, zero calls to `kentender_core.services.authorization`, nothing in `kentender_scope_map`. Strategy and Budget both did; NDS v1.6 did on 4 September. Planning is the last legacy-PE consumer blocking CU-2xx/RM-1xx.
2. Every Planning test world is PE-keyed (seven Playwright PEs, per-test Python PEs); under one-site-one-PE they cannot be created (baseline: `setUpClass` fails on the single-root rule). Isolation moves to a dedicated Fiscal Year + Organisation Units (D13).
3. Four sibling contracts the spec consumes do not exist in code: CFG DPP intake flags, Site PE statutory route, the regulator reference register, Budget `check_plan_affordability`, NDS `Not proceeding`. All are specified and approved in CFG v0.9 / BUD v1.5 / PLN v1.12 and are built in Phase 1 in their owning apps.
4. `Requirement Type` and `Procurement Method` have no production seed — rows exist only through Planning's test fixtures; the §14 seed asserts them but never creates them.
5. The v1.12 artboards were supplied on 5 September (16 modified + DES-14A new), all on the `kentender-industry-82d82607` bundle; DES-09 carries the three-card split and the Baseline schedule card; DES-01 the rebuilt composition. An orphan `industry-f4215206…` bundle reappeared and was removed (no artboard references it).
6. `planning-release-evidence.spec.ts` (10 tests) has no Make gate; `ReturnIssuesDialog.vue` has no component spec.

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| PLN-G00 | Plan, tracker, gap analysis authored; baseline recorded; artboards and sibling docs committed; orphan bundle removed; no product code changed | Done | 2026-09-05. Baseline: `test_planning_v12_schema` Ran 6 FAILED (failures=2); `test_dpp_lifecycle` / `test_planning_workspace` error in `setUpClass` ("Exactly one root organisation unit exists per site"), Ran 0; Playwright not runnable (PE worlds). Orphan `_ds/industry-f4215206…` deleted. Docs written; commit is this phase's. |
| PLN-G01 | Sibling contracts live: DPP flags + commands + job, Site PE route/county, regulator register + read service + seed, registry roles, catalogues seeded, Budget affordability + reference, NDS `Not proceeding`; owning-app tests green; migrate clean | Done | 2026-09-05. PLN-101..109 Done with row evidence; core 25 + 3 + 13, Budget 2, NDS 31 tests OK; migrate clean; no Planning code touched. |
| PLN-G02 | Planning schema + services cut over (D2–D12); Python suite green on the D13 world; migrate clean; retired-concept scan planted-violation-proven; NDS/Budget/Strategy contract suites green | Planned | |
| PLN-G03 | Slice A (DES-01, 02, 03, 04, 05, 06, 16) per rule 6 | Planned | |
| PLN-G04 | Slice B (DES-07, 08, 09, 09A) per rule 6 | Planned | |
| PLN-G05 | Slice C (DES-10, 11, 12, 15) per rule 6 | Planned | |
| PLN-G06 | Slice D (DES-14, 14A, 13) per rule 6; daily job proven | Planned | |
| PLN-G07 | §14 seed rebuilt, idempotent (reset + rerun), validate green; persona browser pass recorded | Planned | |
| PLN-G08 | Full Planning regression, cross-module checkpoint, production build with bundle hash, 17 artboard screenshots + fidelity specs, §16.2 scan, PLN-AC-001..133 mapped, FOLLOW_UPS updated, AUTH tracker CU-2xx marked | Planned | |

## Work register — Phase 0

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-001 | Archive v1.2 companions; author v1.12 plan, gap analysis and this tracker | Done | `git mv` to `*_v1_2*`; three new files in this commit. |
| PLN-002 | Record the Python and Playwright baseline | Done | See PLN-G00. |
| PLN-003 | Confirm artboard set and bundle; remove orphan bundle | Done | 17 `.dc.html` (DES-01..16 + 14A); `grep -ho '_ds/[a-z0-9-]*' *.dc.html` → only `kentender-industry-82d82607…` (36 refs); orphan removed. |
| PLN-004 | Commit supplied v1.12 / CFG v0.9 / BUD v1.5 documents and artboards | Done | This commit. |
| PLN-005 | Arm the two-hourly session wakeup (execution rule 3) | Done | Cron job armed 02:31 EAT, every 2 h at :31. |

## Work register — Phase 1: Sibling contracts

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-101 | `kentender_core/install.py`: `kentender_dpp_submission_open` / `_closes_at` custom fields (D8) | Done | `kentender_core/install.py::_ensure_fiscal_year_flag_fields` adds `kentender_dpp_submission_open` / `_closes_at`; live after `bench migrate` (`get_value(Fiscal Year 2027-2028, [needs_open, dpp_open])` → `[1, 1]`). |
| PLN-102 | `site_configuration.open_dpp_submission` / `close_dpp_submission` / `close_due_dpp_submissions` + hourly hook; `KT_FISCAL_YEAR_REFERENCES` gains Planning doctypes; `get_site_configuration` exposes both intake years | Done | `site_configuration.py`: generic `_open_intake_flag`/`_close_intake_flag`/`_close_due` behind unchanged needs commands + new `open_dpp_submission`/`close_dpp_submission`/`close_due_dpp_submissions`/`get_dpp_submission_state`; `get_site_configuration` exposes `dpp_submission` + route/county; `list_fiscal_years` rows carry DPP flag; disable guard names the DPP flag; `KT_FISCAL_YEAR_REFERENCES` + column-guarded `_reference_count`; hourly hook added. `test_site_configuration` Ran 25 OK (2 new classes: DPP flag independence/atomic move/scheduled close; route derivation/update/rejection). Also fixed a pre-existing test hygiene defect: the suite left the §8 seed's open flags moved onto far-future years (NDS contracts errored in setUpClass until reseeded) — base class now restores them. |
| PLN-103 | Site PE `statutory_approval_route` (four values, required) + `entity_is_county`; seed `Cabinet Secretary`; `site_setup` opens the DPP flag on 2027-2028 (D10) | Done | Site PE JSON gains `statutory_approval_route` (four values) + `entity_is_county`; controller derives a route from `pe_type` when blank (CFG-BR-014, never None); `configure_procuring_entity`/`update_procuring_entity` accept both; `site_setup.SITE` seeds `Cabinet Secretary`; `_seed_dpp_intake` opens the DPP flag on 2027-2028 closing 2026-11-30 23:59:59 EAT. Seed output: `"dpp_intake": "opened: 2027-2028"`. |
| PLN-104 | Regulator reference doctypes + `get_regulatory_reference(fiscal_year)` + §14.1 seed (D9); effective-dating test | Done | New doctypes `Regulatory Reference` (+ child `Regulatory Threshold Band`, `Regulatory Reservation Category`, `Regulatory Market Price`, `Regulatory Schedule Buffer`), immutable after insert, superseding on re-register; `services/regulatory_reference.py::get_regulatory_reference(fiscal_year)` / `register_regulatory_reference`; §14.1 seed (`REG-2027-2028-01`: 33 bands, 10 categories, 30%/20%, 1bn/500m, price index unpublished). `test_regulatory_reference` Ran 3 OK (unavailable-without-raise, category-keyed matrix + immutability + supersession retained, canonical seed figures). |
| PLN-105 | Registry: Finance Confirmation Officer for Planning; retire `Planning Auditor`; citations → v1.12 (D6) | Done | Registry: `Planning Auditor` retired, `Auditor` cites PLN v1.12, `Budget Officer` loses `finance_confirmation`, `Finance Confirmation Officer` cites PLN v1.12 §6, Accounting Officer / Plan Statutory Approver / Procurement Planner → v1.12. `test_business_role_registry` Ran 13 OK (one-auditor test replaces the both-labels test). |
| PLN-106 | Core seed for `Requirement Type` (4 incl. Works) and `Procurement Method` (11) | Done | `site_setup._seed_catalogues`: 4 Requirement Types (incl. Works) + 11 Procurement Methods; seed output `"catalogues": {"created": 15, ...}`. |
| PLN-107 | Budget `check_plan_affordability` + `reference` in `list_eligible_budget_lines`; request-shaped tests (D11) | Done | `budget_line_contracts.check_plan_affordability(fiscal_year, planned_totals)` (dict or rows; per-line approved/planned/positions/as_at; blocking within-approved with exact excess; advisory within-available; unknown lines fail closed) + `reference` on `list_eligible_budget_lines`; whitelisted in `budget_api`. `test_bud_chg_001_v15_affordability` Ran 2 OK (evaluated as system principal — Planning's gateway posture). |
| PLN-108 | NDS `Not proceeding` usage value with reason (D12) | Done | NDS `USAGE_NOT_PROCEEDING`, projection Select + `not_proceeding_reason`, `project_planning_usage(not_proceeding_reason=)` mandatory for that outcome. `test_departmental_needs_contracts` Ran 31 OK (new not-proceeding test). |
| PLN-109 | `bench migrate` clean; owning-app focused suites green; seeds idempotent | Done | `bench migrate` clean (after_migrate hooks ran); `site_setup.run` twice → existing/updated, no duplicates (`REG-2027-2028-01 (existing)` on rerun path); suites listed above green. |

## Work register — Phase 2: Planning cutover

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-201 | Schema: `fiscal_year` replaces the three context fields on every doctype; rekeyed uniques; DocPerm role changes (D6/D3); `unit` → UOM | Planned | |
| PLN-202 | Schema: drop `Departmental Plan Submission Window`, `Plan Reservation Reference`, `finance_state`, seven flat dates; Plan Item §4.9 fields; `Plan Item Forecast Revision`; Finance task/decision re-keyed to Version; Version `splitting_confirmation` / `late_activation_reason`; entry `not_proceeding_reason` | Planned | |
| PLN-203 | Patch set `pln_chg_001_v112_*` (drop columns/doctypes and tables; uniques); migrate clean | Planned | |
| PLN-204 | `planning_authorization.py` + all call-site conversions; `authority.py` deleted; hooks scope map + permission hooks (D2–D5) | Planned | |
| PLN-205 | `planning_context.py` FY-only; `dpp_lifecycle` flag + not-proceeding + coverage rule; `dpp_validation` publishes `Not proceeding` | Planned | |
| PLN-206 | `schedule.py`: baseline derivation, floors/ceilings, delivery boundary, cascade preview/confirm, health count, `CheckApproachingMilestones` + daily hook | Planned | |
| PLN-207 | `readiness.py`: admissibility, contents, reservation/county shares, splitting advisory, `PLN_REFERENCE_UNAVAILABLE`; `ConfirmSplittingAdvisory` (O1) | Planned | |
| PLN-208 | `plan_finance.py` rewritten to one task per Version over affordability; Finance-stale rule | Planned | |
| PLN-209 | `plan_governance.py`: route from Site PE, `PLN_STATUTORY_ROUTE_UNCONFIGURED`, late-activation reason (O2), corrected-submission Finance-repeat rule | Planned | |
| PLN-210 | `plan_publication.py`: OCDS payload, forecast seeding, reservation code removed; `budget_gateway` trimmed; `strategy_gateway` PE kwarg dropped | Planned | |
| PLN-211 | `api.py` new/changed endpoints; `errors.py` full §9 | Planned | |
| PLN-212 | `tests/fixtures.py` on FY 2101-2102/2103-2104 (D13); all 14 modules updated in place; §16.2 evidence tests; schema allow-lists + token scan (planted-violation) | Planned | |
| PLN-213 | Planning Python regression green; NDS architecture/events, Strategy consumer, Budget contract, core authorization suites green | Planned | |

## Work register — Phases 3–6: UI slices

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-301 | Slice A read models + components from DES-01, 02, 03, 04, 05, 06, 16 (class-for-class) | Planned | |
| PLN-302 | Slice A component specs + fidelity specs | Planned | |
| PLN-303 | `playwright_ui_fixtures.py` D13 world + `reset_all`; workspace / dpp / dpp-review specs; globalTeardown; Make gates | Planned | |
| PLN-304 | Slice A browser click-through per rule 6 | Planned | |
| PLN-401 | Slice B components from DES-07, 08, 09, 09A | Planned | |
| PLN-402 | Slice B component + fidelity specs | Planned | |
| PLN-403 | plan-workbench spec | Planned | |
| PLN-404 | Slice B browser click-through | Planned | |
| PLN-501 | Slice C components from DES-10, 11, 12, 15 | Planned | |
| PLN-502 | Slice C component + fidelity specs | Planned | |
| PLN-503 | finance / governance specs | Planned | |
| PLN-504 | Slice C browser click-through | Planned | |
| PLN-601 | Slice D components from DES-14, 14A, 13 | Planned | |
| PLN-602 | Slice D component + fidelity specs | Planned | |
| PLN-603 | publication spec incl. cascade | Planned | |
| PLN-604 | Slice D browser click-through; daily job proven live | Planned | |

## Work register — Phase 7: Seed

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-701 | `seeds/kentender_mvp_v1.py` rewritten: prerequisites, §14.2 actors (O4), integrated baseline through real commands, no reservations | Planned | |
| PLN-702 | Isolated profiles rebuilt; KEBS fails loudly (O5) | Planned | |
| PLN-703 | Orchestrator / validate / purge wiring; idempotent rerun with count snapshots | Planned | |
| PLN-704 | §14-persona browser pass | Planned | |

## Work register — Phase 8: Release

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-801 | Full Planning regression (Python, vitest, Playwright single-worker) | Planned | |
| PLN-802 | Cross-module checkpoint | Planned | |
| PLN-803 | Production build; bundle hash confirmed | Planned | |
| PLN-804 | Evidence pack: 17 screenshots at 1440×1024; fidelity specs | Planned | |
| PLN-805 | §16.2 repository scan | Planned | |
| PLN-806 | PLN-AC-001..133 mapped; FOLLOW_UPS updated; AUTH tracker CU-2xx marked; memory updated; cron deleted | Planned | |

## Acceptance map

Completed at Phase 8 (PLN-806). PLN-AC-046 is expected to stay Open (O5).
