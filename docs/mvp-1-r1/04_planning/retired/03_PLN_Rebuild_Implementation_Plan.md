# PLN-CHG-001 v1.2 → v1.12 — Procurement Planning correction plan

| Control | Value |
|---|---|
| Authority | `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_12.md` (approved 3 September 2026; supersedes v1.11 and all earlier versions in full) |
| Sibling authorities consumed | AUTH-ADR-001 v1.6, KT-STD-001 v1.1 (v1.2 §3A rules carried by PLN-AC-111..113), LAW-REG-001 v1.0, CFG-CHG-002 **v0.9**, BUD-CHG-001 **v1.5**, NDS-CHG-001 v1.6, STR-CHG-001 v1.6 |
| Companions | `02_PLN_Rebuild_Gap_Analysis.md` (current-state facts), `IMPLEMENTATION_TRACKER.md` (evidence ledger) |
| Predecessor cycle | v1.2 rebuild, closed 31 August 2026 — archived as `03_PLN_Rebuild_Implementation_Plan_v1_2.md`, `02_PLN_Rebuild_Gap_Analysis_v1_2.md`, `IMPLEMENTATION_TRACKER_v1_2_closed.md` |
| Prepared | 5 September 2026 |
| Status | Approved by the Project Owner 5 September 2026 with three execution rules (§7) |

## 1. Governing approach

**Correction in place with targeted demolition.** The v1.2 module is three days old, fully tested and structurally right; v1.12's §1.1 register renames or removes concepts inside a model whose aggregates (DPP, Annual Plan, Plan Item, allocations, governance, publication, requisition eligibility) survive. Roughly 60% of the v1.2 code survives untouched in mechanics. What is demolished is demolished precisely: the per-item Finance and reservation subsystem, the `Departmental Plan Submission Window` doctype, every PE/context field, the private authoriser `services/authority.py`, and the seven per-PE Playwright fixture worlds.

**Efficiency is the point of this plan.** The last two cycles lost their hours to verification-last ordering, artboards ported from prose instead of markup, per-PE fixture worlds that no longer exist, batch test rewrites and full-suite diagnostics. Every phase below is shaped against those sinks, with a time target that is a contract: a phase overrunning its target by half stops and records why before continuing.

## 2. Decision register

| # | Decision | Why |
|---|---|---|
| D1 | Correction in place per §1.1; no alias, dual-read, compatibility field or flag. Deletion lands in the phase of its replacement. | Spec posture; proven mechanics are kept, not rewritten. |
| D2 | Authorisation = `kentender_core.services.authorization` (`authorise_record`, `permitted_ou_scopes`, `assignment_snapshot`, `is_technical`). New `services/planning_authorization.py` replaces `authority.py`, which is deleted. Budget's `budget_authorization.py` is the shape; DPP roles pass a real `organisation_unit`. Order inside every command: SoD pre-check → `authorise_record` → task/state. | §6, §16.4; NDS v1.6 D2 precedent. |
| D3 | `kentender_scope_map` registers only the DPP family read by OU-scoped roles: `Departmental Plan` (`organisation_unit`); `Departmental Plan Version`, `Entry`, `Submission`, `Validation Decision` through Planning-side `permission_query_conditions`/`has_permission` wrappers that resolve the root OU and delegate to core. Annual Plan family stays unregistered after Departmental Author / Head of User Department are removed from `Annual Plan` and `Annual Plan Version` DocPerms. `Annual Plan Publication Destination` is never registered. No denormalised OU column. | CU-302 finding (Site-wide-only doctypes must not be registered); §2.2 data-purpose gate forbids a permission-only column. |
| D4 | AUTH_* → PLN_* remap at the service boundary: record-addressed reads/commands mask to not-found; context/creation → `PLN_NO_CONTEXT`; segregation → `PLN_SEGREGATION_CONFLICT`; task/state → `PLN_REVIEW_STALE`; period → `PLN_WINDOW_CLOSED`. No `PLN_SCOPE_DENIED`. | §9 masking; NDS D10 precedent. |
| D5 | §6.1 maker-checker is evaluated from existing evidence: chain = closure over `correction_of_plan_version`; Planner actors from `submitted_by_user`, the owner of non-correction versions and `Planning Command Journal.actor` for Planner commands; Finance and AO actors from decision rows. The Command Journal is therefore segregation evidence and is never wiped globally. | No new field passes the data-purpose gate. |
| D6 | Roles: the Planning Finance task is gated on **Finance Confirmation Officer**; `Planning Auditor` is retired from the registry and every Planning DocPerm in favour of **Auditor**; `Plan Statutory Approver` remains the registered statutory capacity; Budget Officer loses Planning DocPerm read. Registry citations bumped to v1.12. | §6, §14.2, BUD v1.5 §7. |
| D7 | One Link `fiscal_year` → ERPNext `Fiscal Year` replaces `pe_fy_context`, `procuring_entity` and `financial_year` on every Planning doctype; uniques rekeyed (DPP `fiscal_year + organisation_unit`; Annual Plan `fiscal_year` unique). Field names stay plain (`organisation_unit`, `fiscal_year`, `unit`). | §1.1 v1.5 rows; NDS D7 (no `_id` churn). |
| D8 | DPP intake = Custom Fields `kentender_dpp_submission_open` / `_closes_at` on Fiscal Year added in `kentender_core/install.py::_ensure_fiscal_year_flag_fields`, with `site_configuration.open_dpp_submission` / `close_dpp_submission` / `close_due_dpp_submissions` mirroring the needs flag. `Departmental Plan Submission Window` is dropped by patch. No System setup UI this cycle — CFG v0.9 §10 draws none. | CFG v0.9 §4.2, CFG-BR-013. |
| D9 | Regulator reference register = effective-dated `kentender_core` doctypes per CFG v0.9 §4.4A (threshold matrix rows keyed category × method × Fiscal Year; reservation categories + target; exclusive-preference thresholds; market price index) plus `get_regulatory_reference(fiscal_year)` and the §14.1 seed. Server + seed only; no UI. Planning stores the resolved band on the item. | CFG v0.9 §4.4A, CFG-BR-015/016; PLN §7.5. |
| D10 | Site PE gains `statutory_approval_route` (four values, no None) and `entity_is_county`; seeded `Cabinet Secretary`. Planning's governance capacity resolution reads it. | CFG v0.9 §4.1, CFG-BR-014; PLN §4.12. |
| D11 | Budget adds `check_plan_affordability(fiscal_year, planned_totals)` per BUD v1.5 §8.2 and returns `reference` from `list_eligible_budget_lines` (closes FU-02). Planning's `budget_gateway` keeps only those two; check/reserve/release/revalidate paths are deleted. | BUD v1.5 §8.2, §9.1; PLN §7.3. |
| D12 | NDS `USAGE_VALUES` gains `Not proceeding` (with reason) on `project_planning_usage`; Planning publishes it on DPP acceptance for entries carrying `not_proceeding_reason`. | PLN-AC-092. |
| D13 | Test isolation without PEs: one Playwright world — FY `2098-2099`, OUs `Playwright — Procurement Planning` / `Playwright — Planning Outsider`, eight actors granted through `responsibility_administration.grant`, namespace `KENTENDER_PLAYWRIGHT`; `reset_all()` deletes by namespace or by `fiscal_year = 2098-2099` in child→parent order and purges journal rows and Notification Logs for the PW actors; the DPP flag moves to the PW year once per run and is restored to `2027-2028` by Playwright `globalTeardown` and at the end of each Make gate. `--workers=1` and `serial` on every spec. Python `tests/fixtures.py` uses FY `2101-2102` (open) / `2103-2104` (closed), namespace `KENTENDER_TEST`, same shape. The Python suite and Playwright never run concurrently. | AUTH v1.6 removes per-spec PEs; one Annual Plan per FY; one open flag at a time. |
| D14 | Artboards are the literal build source, ported class-for-class from each `.dc.html`; a design-fidelity spec per artboard is a slice-gate condition. Reusing an existing component for a screen whose artboard changed means re-porting from the artboard. | AGENTS.md §6.6; owner-mandated fidelity gate. |
| D15 | DES-13 Publication result is built (artboard supplied; closes FU-06's design gap). `RemovePlanItemInSuccessor` / `CancelPlanUpdate` stay UI-less (no artboard). | §11.15. |

### 2.1 Owner decisions proceeding on defaults (execution rule 1)

| # | Question | Default applied |
|---|---|---|
| O1 | Where the splitting-advisory confirmation is stored (PLN-AC-073/074; §4 defines no field or command) | `splitting_confirmation` Small Text on `Annual Plan Version`, written by a `ConfirmSplittingAdvisory` command, shown on the DES-07 readiness row. |
| O2 | Who supplies the late-activation reason (invariant 27, PLN-AC-076) | `SubmitConsolidatedPlan` / `SubmitCorrectedPlan` require `late_activation_reason` when the Fiscal Year has begun at submission; stored on the Version. |
| O3 | `item_status` vocabulary (Third Schedule column 17) | Governed Select `Not started` / `In progress` / `Completed` / `Cancelled`; derived from actuals where present, `Not started` otherwise. |
| O4 | Statutory persona | Daniel Rotich (`daniel.rotich@moh.example.test`) replaces `moh.plan.approver@example.test`; `.env.ui` gains keys for the Planning personas. |
| O5 | KEBS profiles (FU-01) | Remain blocked by design; PLN-AC-046 stays Open. |
| O6 | Orphan `_ds/industry-f4215206…` bundle | Deleted in Phase 0 (no artboard references it). |

## 3. Phase sequence

| Phase | Name | Target | Exit condition |
|---|---|---|---|
| 0 | Plan, tracker, baseline | this session | Docs committed; baseline recorded verbatim; orphan bundle removed; no product code changed. |
| 1 | Sibling contracts (horizontal, additive) | ½ day | Owning-app focused tests green; `bench migrate` clean; seeds idempotent; no Planning code changed. |
| 2 | Planning domain + services cutover (horizontal) | 1 day | Planning Python suite green on the D13 fixture world; migrate clean; retired-concept scan planted-violation-proven; NDS/Budget/Strategy contract suites green. |
| 3 | Slice A — Workspace + DPP (DES-01, 02, 03, 04, 05, 06, 16) | ½ day | Slice gate (§4). |
| 4 | Slice B — Workbench + Plan Item (DES-07, 08, 09, 09A) | ½ day | Slice gate. |
| 5 | Slice C — Finance + governance (DES-10, 11, 12, 15) | ½ day | Slice gate. |
| 6 | Slice D — Active plan + publication (DES-14, 14A, 13) | ½ day | Slice gate. |
| 7 | §14 seed + persona pass | ½ day | Seed + validate green twice; persona browser pass recorded. |
| 8 | Release verification + sign-off | ½ day | Full Planning regression, cross-module checkpoint, production build with bundle hash, 17 artboard screenshots + fidelity specs, §16.2 scan, PLN-AC-001..133 mapped, FOLLOW_UPS updated, AUTH tracker CU-2xx rows marked. |

### Phase 1 detail
- `kentender_core`: DPP flag fields + commands + hourly job (D8); Site PE `statutory_approval_route` + `entity_is_county` + seed (D10); regulator reference doctypes + read service + §14.1 seed (D9); registry role changes (D6); `Requirement Type` (+ Works) and the eleven `Procurement Method` rows seeded in core; `KT_FISCAL_YEAR_REFERENCES` gains `Departmental Plan` / `Annual Plan`.
- `kentender_budget`: `check_plan_affordability` + `reference` (D11), request-shaped tests.
- `departmental_needs`: `Not proceeding` usage value (D12).

### Phase 2 detail
- Schema: D7 everywhere; drop `Departmental Plan Submission Window`, `Plan Reservation Reference`, `finance_state`, the seven flat `*_date` fields; Plan Item gains the §4.9 fields (category, horizon, justification, aggregation, lotting, lot count, county reservation, reservation category + reason, exclusive preference, threshold band, baseline anchor + five periods, 7 baseline / 7 forecast / 7 actual dates, `item_status`); new `Plan Item Forecast Revision`; `Plan Finance Task` / `Decision` re-keyed to the Version with the affordability statement; `unit` → ERPNext `UOM`; `Annual Plan Version` gains `splitting_confirmation`, `late_activation_reason`. One `pln_chg_001_v112_*` patch set (drop columns, doctypes **and tables**; rekeyed uniques). Schema test allow-lists and prohibited-token scan updated (`pe_fy_context`, `procuring_entity`, `User Permission`, `Funding Reservation`, `Departmental Plan Submission Window`, `Budget Officer`).
- Services: `planning_authorization.py` (D2–D5) and the ~60 call-site conversions; `planning_context.py` → FY filter only; `dpp_lifecycle` window → flag, `not_proceeding_reason`, coverage rule "planned or not proceeding"; new `schedule.py` (baseline derivation with governed floors/ceilings, delivery-boundary check, cascade preview/confirm, schedule health, `CheckApproachingMilestones`); new `readiness.py` (method admissibility, reservation and county shares, splitting advisory, contents completeness, `PLN_REFERENCE_UNAVAILABLE`); `plan_finance.py` rewritten to one task per Version over `check_plan_affordability`; `plan_governance.py` route from Site PE + `PLN_STATUTORY_ROUTE_UNCONFIGURED` + corrected-submission Finance-repeat rule; `plan_publication.py` OCDS payload, forecast seeding on activation, reservation release removed; `budget_gateway.py` trimmed; `strategy_gateway.py` PE kwarg dropped; `errors.py` = full §9; `hooks.py` scope map + hooks + daily scheduler.
- Tests updated in place per module as each service changes; §16.2 evidence tests added; request-shaped tests for every new or changed endpoint.

## 4. Slice gate (Phases 3–6)

Every slice, in this order: read every `.dc.html` for the slice → read-model deltas → port components class-for-class → vitest component specs (exact fields, absent fields, action visibility, dialog copy) → design-fidelity spec per artboard → Playwright spec on the D13 world (per-role login incl. one out-of-scope actor, absence assertions on refusal paths, pinned instants) → real browser click-through (first paint and one interactive re-render, zero page console errors). `touch hooks.py`, clear cache and confirm the bundle hash changed after asset edits.

| Slice | Notable deltas |
|---|---|
| A | DES-01 rebuilt (inline FY filter, headline-plus-button card, amber notice, retitled table, schedule-health count when an Active plan exists); no PE selector; not-proceeding control on Need-origin rows; Forbidden panel copy + verdict-before-render (PLN-AC-111..113); DES-06 type select from the four-type catalogue. Specs: workspace, dpp, dpp-review. |
| B | DES-07 nine-row readiness card, Reserved-share strip cell, version-level Finance button; DES-09/09A three cards, Preference and structure card, live-recomputing Baseline schedule card with closed disclosure; method select limited to the admissible set; value band; price-index helper. Spec: plan-workbench. |
| C | DES-10 affordability table with As-at and green notice; DES-11/12 ten-column immutable table with Reservation and Funding columns and the advisory line; Board resolution reference. Specs: finance, governance. |
| D | Schedule card with baseline/forecast/actual tiers and em-dash actuals; schedule-health strip cell; 640 px cascade dialog; DES-13 with System Manager retry. Spec: publication. |

## 5. Efficiency rules (standing)

1. Never rewrite a surviving service or test module; edit in place and keep proven mechanics.
2. Open the artboard before touching any component; port markup, never re-compose from prose or from the previous build "minus PE".
3. One fixture world, reset per spec, serial; no new PE or FY per spec; no `now`-relative instants.
4. Tests travel with the code in the same phase; the full suite runs once at Phase 8 (and the Python half once at the end of Phase 2). Diagnose by focused reproducer only.
5. Before any seeding or fixture campaign check RQ queue depth and the flag state; never restore the demo seed without asking.
6. Owner questions are limited to §2.1; everything else follows the spec's default-to-omit rule.

## 6. Verification commands

```bash
# Python (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.<module>
bench --site kentender.midas.com run-tests --app kentender_core --module kentender_core.tests.test_authorization

# Components + browser (repo root)
npx vitest run --project procurement-planning
npx playwright test tests/ui/smoke/planning/<spec>.spec.ts --workers=1
npx playwright test tests/ui/smoke/design-fidelity/planning-fidelity.spec.ts

# Seeds / build
make seed-kentender-mvp-v1 SITE=kentender.midas.com && make seed-kentender-mvp-v1-validate SITE=kentender.midas.com
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_procurement
```

## 7. Execution rules (Project Owner, 5 September 2026)

1. Phases 0–8 run continuously without pausing for confirmation; §2.1 defaults apply and are recorded for later reversal.
2. Every phase (and every UI slice) ends in one commit with the tracker updated in the same commit.
3. A two-hourly session wakeup is armed so a stall caused by usage limits resumes from the tracker's first non-Done row.
