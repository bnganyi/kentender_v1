# PLN-CHG-001 v1.23 — Procurement Planning implementation — tracker

**Authority:** `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_23.md` (17 September 2026).
**Companion:** `PLN-CHG-001_Implementation_Plan.md` (decisions D1–D12, consistency findings C1–C9, phase design, slice gate, commands, traps, non-goals).
**Design source:** `design/*.dc.html` — 15 files, 112 panels = 111 MVP artboards + the U15 deferral notice. Variant id = the accent badge text above each sheet.
**Supersedes-in-tracking:** `retired/PLN-CHG-001_IMPLEMENTATION_TRACKER_v1_18.md` — the v1.18 cycle, Phases 0–2 closed and Phase 3 slices 302–306 built (uncommitted), stopped at PLN18-307 because the requirements were superseded. That build is the baseline this cycle corrects.
**Status:** In progress, 18 September 2026. Phase 0 and Phase 1 closed. Phase 3's seed was brought forward and repaired because every remaining slice needs a live world to verify against. Slices 2A–2H are built, each verified in a real browser against the canonical world and committed; what each still owes is on its own gate row. Slice 2I (U14/U16), slice 2J (C01–C04) and the U08 formation dialog are built. The nine browser specs are green (PLN22-G13b). The per-artboard fidelity gate is green (PLN22-G13a, 22/22) and the Planning Python suite re-run clean (PLN22-G13c, 311 tests). Phase 3's remainder and the Phase 4 release evidence remain.
**Started:** 18 September 2026.

---

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Partial` / `Done`. Reversed decisions are struck through in place.
2. `Done` requires the row's own evidence: a command with result counts, a named test, a diff, or a described browser observation with literal rendered strings. Never record a result that was not observed.
3. A row touching a file that still references a §16-prohibited concept is not `Done`. Prohibited: a Procuring Entity selector or scope argument, an FY user grant, `User Permission` or a bare Frappe Role as authority, a task as permission, a client-only lifecycle guard; a mandatory Need on a direct requirement, a partial accepted-Need allocation, a fabricated residual source, a source-less item, a direct-source identity regenerated on copy; any Planning Budget reservation/release/revalidation call, `PLN_RESERVATION_RELEASE_FAILED`; an optional statutory route, Planner/HOPF equivalence, an extra HOPF approval state, a segregation reset across a correction chain; an editable submitted/approved/Active baseline, source-cohort expansion through correction, allowance reset on copy, a later source absorbed into a scope-locked item; a client-supplied `procurement_category`, an in-place accepted-classification edit, a purchase-editor classification override, silent item reclassification; implied coverage or fulfilment from plan inclusion or a Tender badge; universal method timing constants, a missing-profile fallback, a hard-coded unverified legal threshold, a Plan-total reservation denominator, a reason-only waiver; `highest_advantage`, `exclusive_preference`, a preference override, `Multi-year` / `multi_year_justification`, `ocds` / `ocid`; a user-entered actual, an unqualified item-level actual, missing-to-zero variance, a per-day reminder key; **any U15 route, forecast-cascade control, forecast-driven reminder surface or unsupported completion placeholder**; synchronous external publication inside `approve_annual_plan`, blind retry/withdrawal on an unknown outcome, a fabricated acknowledgement, forced activation of held content; `Procedure — Planning example`, resolver status, `Rule version` or `Source check` as an **ordinary business field** (inside a collapsed `Supporting details` disclosure is permitted, §10.8); a displayed `None` / `Not applicable` / `no restriction` / `Single lot` / `Lot count 1` shown only to prove storage; summary-only governance, a forced accordion or download prerequisite, delimiter-crammed facts, duplicate sidebar chrome, a prototype harness; disposal content; `Awaiting Finance` or `Confirmed` as a Plan **status** (as a work-status label on a Draft it is permitted, §5.2.2); `RecordRequisitionDrawdown` / `record_requisition_drawdown`; Stitch or Civic Ledger markup, `kt_cl_surface_registry.js` entries, sidebar work-queue entries, `showPeSwitcher: true`.
4. No row may introduce an alias, redirect, dual-write, compatibility shim or parallel legacy+new surface. Deletion lands in the same slice as its replacement.
5. Screens are built from `design/*.dc.html` class-for-class, one variant id per screen state; behaviour from §§9, 11 and 11.9, never from artboard content. Reusing a component for a state whose artboard differs means re-porting it. Fixture text in an artboard is exempt from fidelity; structure and geometry are not.
6. Slice gates (`PLN22-G04`..`PLN22-G13`) close only on the plan's §4 slice gate — all ten conditions, including the live browser pass and the changed bundle hash.
7. Static and architecture guards are `Done` only when proven by a planted violation.
8. Fixture instants are pinned to §10.2/§13.1 (24 Nov – 20 Dec 2026 EAT) under the frozen clock, never `now`-relative. The Python suite and Playwright never run on the site at the same time — both move the intake flags. A row claiming a cross-app file is unaffected cites the specific `file:line` checked.
9. Diagnosis follows the KT-STD-001 §5 ladder; a full-suite run is never the first diagnostic step. A phase overrunning its target by half stops and records why.
10. Sibling contract code is built in the owning app with owning-app tests and tagged `[core]` `[budget]` `[nds]` `[req]` `[tpr]`; sibling specification amendments are follow-ups, not rows (D10).
11. Nothing seeded carries `verification_status = Verified`. The canonical seed uses `Fixture-verified — not production law` (D9) and every screen that shows a rule shows that status.

---

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-18 | D1–D12 as recorded in `PLN-CHG-001_Implementation_Plan.md` §3. | See plan. |
| 2026-09-18 | **C1 closed by v1.23.** `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION` supplied; §10.5 gains a classification design-asset gate; `PLN23-AC-002` forbids U09 as a substitute. | Owner supplied the artboards. |
| 2026-09-18 | **C2 closed by v1.23.** `PLN23-CHG-001` defers AC-119 and AC-124..131 entirely, deletes the two forecast error codes, removes the cascade service entries and replaces §7.5 with an explicit no-service rule. D7 is now the specification, not a judgement call. | Owner consistency correction. |
| 2026-09-18 | Owner instruction: implement all phases nonstop without further prompting. | — |

---

## Headline findings (read before touching code)

1. **This is a delta cycle, not a rebuild.** The v1.18 domain implements the business rules v1.22 retains. 36 doctypes, 31 services, 61 whitelisted endpoints, 16 test modules, `planning-domain-gate` green at v1.18 Phase 2 exit.
2. **New domain work is confined to classification** (v1.21): server-derived Category, the `DPP Classification Correction` record, its command and read, the allocation classification snapshot, the effective projection and the four affected-item recovery outcomes.
3. **The UI is entirely superseded.** v1.20 replaced §10 with exact artboard contracts and v1.22 reduced the first views. Eight families have an existing screen to delete and re-port (U01, U02–U05, U06, U07, U08, U09, U10, U21); U11, U12, U13, U14 and U16 are greenfield against v1.22 (their current files are v1.12 remnants); C01–C04 is new Planning-side panelling.
4. **The uncommitted working tree matters.** Planning last committed at `0c4b6a54`. PLN18-303..306 and the v1.18 artboard deletions are uncommitted. Checkpoint before deleting (D3).
5. **Design-system CSS is already in core.** `kt_industry_tokens.css` defines `kt-notice`, `kt-disclosure`, `kt-kpi-card`, `kt-record`, `kt-checkbox`. Only the artboards' own Desk-chrome simulation is absent, and Desk supplies that.
6. **Routes are unchanged.** The four existing Pages cover every §9.2 route family, so no new Page and no `bench migrate` requirement for routing.
7. **Two residues to remove:** `exclusive_preference` on `Annual Plan Item` (+ `plan_governance.py:542`), and fourteen unused item-level `forecast_*`/`actual_*` date columns.
8. **Artboards are clean** on the §16 prohibited-copy sweep. `Rule version` / `Source check` in U09 sit inside the collapsed `Supporting details` disclosure, which §10.8 permits.
9. **Artboards left some fixture values blank** rather than inventing them (PLN20-AC-008 honoured). Phase 3 must supply each one — see the Phase 3 register.
10. **No RQ worker on this bench.** Publication must run inline under tests and seeds.

---

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| PLN22-G00 | Phase 0: plan + tracker written; v1.18 docs retired; `evidence/v1_23/` created with `FRAMES.md`; checkpoint commit of the uncommitted v1.18 UI; no product code changed | Done | 2026-09-18. Docs retired into `retired/`; `evidence/v1_23/FRAMES.md` lists 112 panels across 15 files, no duplicates; checkpoint commit `06249aa6`. Owner questions did not need asking — v1.23 answered both. |
| PLN22-G01 | Phase 1A: classification provenance and correction — record, command, read, projection, allocation snapshot, four recovery outcomes, error codes; `test_dpp_classification_correction` green | Done | 2026-09-18, commit `f1b2feb6`. `DPP Classification Correction` doctype; `dpp_classification.py`; category moved onto the `Requirement Type` catalogue with a patch; allocation classification snapshot; three new error codes. `test_dpp_classification_correction` 18/18. |
| PLN22-G02 | Phase 1B–1C: forecast/cascade/reminder facility removed; residues removed with patch; `test_planning_v123_schema` planted-violation-proven | Done | 2026-09-18, commit `f1b2feb6`. Went further than "unreachable": the two retired doctypes, the cascade service and endpoints, the scheduler job, the milestone-notice producer, the 14 item-level forecast/actual columns and `exclusive_preference` are all gone, with `pln_chg_001_v123_drop_forecast_facility`. `test_planning_v123_schema` 12/12, planted violation proven. Error messages regenerated from the v1.23 §8 table. |
| PLN22-G03 | Phase 1 exit: `make planning-domain-gate` green; three clean `bench migrate`; cross-module checkpoint | Done | 2026-09-18. 16 Planning modules, 262 tests, all OK. Three consecutive clean migrates. Budget `test_bud_chg_001_v19_usability` 18/18. One pre-existing unrelated failure recorded: `kentender_core` `test_industry_design_gate` on `TechnicalSearch.vue` (root is `class="kt-industry kt-setup-root"`, the gate greps the exact string `class="kt-industry"`). Untouched by this cycle. |
| PLN22-G04 | Slice 2A — U01 workspace (6 artboards); U21 states carried by the shared components | Partial | 2026-09-18, commit `3f5db2c7`. U01 re-ported and verified live as Mercy (first paint, an interactive re-render switching financial year and back, browser back/forward, zero page console errors); `evidence/v1_23/U01-CURRENT.png`. 13 component tests, 20 workspace service tests. Browser spec green (G13b); fidelity green (G13a). **Owed:** the U21 variants as their own fidelity assertions. |
| PLN22-G05 | Slice 2B — U02–U05 departmental preparation and certification (13 artboards) per rule 6 | Partial | 2026-09-18, commit `dd589569`. Screen re-ported for both the Author and HoD readings; row wording, separate Quantity/Unit, always-visible exclusion reasons and returned comments. Verified live as Peter on the HRMD plan, zero console errors. 11 component tests, 18 read tests. **Owed:** U03/U04 entry-editor re-port, fidelity assertions, browser spec. **U03/U04 closed 2026-09-18, commit `fc1c9202`.** Funding now opens beneath its own row instead of navigating away, with the requirement summarised, the six facts one disclosure away, the budget line by name with its code beneath, and the cost helper at the cost field; the exclusion keeps its own governed dialog. Row actions now say what the department will do (`Enter funding details` / `Review details` / `View details` / `Include in this year's departmental plan`) — one of those labels was already being matched for in the browser and had never once matched, so the restore branch could not fire. A Planner reading another department's plan now gets no action rather than a link into a masked denial. The editor page is U04 alone. 19 component tests. Verified live as Grace on a departmental update: panel in place with both rows visible, save wrote through to KES 85,000,000, canonical world rebuilt after. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G06 | Slice 2C — U06 validation + classification correction (8 artboards) per rule 6 | Partial | 2026-09-18, commit `2f81b1e7`. Both screens built; Requirement type is the only classification input and Category is derived text. Proven end to end in the browser as Mercy: corrected the infrastructure requirement and confirmed on the server that the Active Plan Item, the allocation snapshot and the accepted decision were all untouched — only the correction appended (PLN21-AC-005 live). Site reseeded after. 23 component tests. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G07 | Slice 2D — U07 annual plan preparation (7) + U08 add requirements (4) | Partial | 2026-09-18, commit `3d08b6b2`. U07 re-ported: purchases lead and name their own next work, three Plan checks, no tabs, no premature approval section. Two real defects fixed — `Prepare plan update` only navigated instead of invoking the guarded successor start, and the cancel dialog had neither the required reason nor the v1.23 copy. Verified live: created the update from the workspace and cancelled it with a reason, current plan still in force. 18 component tests. **Owed:** U08 formation dialog re-port, fidelity assertions, browser spec. **U08 closed 2026-09-18, commit `e47941c7`.** Selection shown as fact rather than re-offered as checkboxes; the combination reason and the purchase title are asked at the moment of combining and go into the formation command, so a combined purchase is complete when it exists instead of arriving with a readiness blocker and a "+"-joined title. The compatibility rule is now the command's own (same budget — not line — requirement type, unit and kind), exposed as a per-source key; the old browser-side same-budget-line test would have refused legitimate combinations the server allows and has a test for. Units never merge. A scope-locked source is named unavailable and cannot be added. 4 server + 10 component tests; canonical world rebuilt on the new path. Browser spec green (G13b); fidelity assertions green (G13a). **Still owed:** the live click-through (the current plan has no unallocated requirements). |
| PLN22-G08 | Slice 2E — U09 purchase editor (7 artboards) per rule 6 | Partial | 2026-09-18, commit `e6e444c1`. First view cut to the five decision sections; resolver status, rule version, source check and the repeated reservation arithmetic removed from ordinary view; None / Single lot / Lot count 1 / inapplicable county / fixed horizon all omitted. Verified live against the rendered page — none of the prohibited strings present. 19 component tests. Browser spec green (G13b); fidelity assertions green (G13a). **Owed:** U09-LOCKED and the two classification variants against real downstream evidence. |
| PLN22-G09 | Slice 2F — U10 funding review and reassessment (7 artboards) per rule 6 | Partial | 2026-09-18, commit `930395af`. Approved/planned/difference/result first view; balances collapsed and labelled advisory; low availability advisory versus approved excess blocking, both visible and distinct. Verified live as Josphat. 12 component tests. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G10 | Slice 2G — U11 governance review (9) + U12 source evidence (4) | Partial | 2026-09-18, commit `00daf535`. **Found that the governance review had never rendered at all**: `ReviewScreen`, `ReturnPlanDialog` and `SourceEvidenceScreen` were used in the shell template but never imported, so the route resolved, the server returned correct data and the page painted nothing. U11 built: one document for every actor, decision summary and issues before the decision, nothing expanded, evidence closed but complete. A server-side decision summary now assembles value/purchases/departments, the three check results and the exact issue list once. Verified live as Amina. 14 component tests. **Owed:** U12 re-port, fidelity assertions, browser spec. **U12 closed 2026-09-18, commit `88e26522`.** It had been dead in three places at once — no `governance-source` screen value, `sourceEvidence` bound but never declared, and the review's `view-evidence` handler named but never written — so the correct, tested server read could never be opened. Rebuilt and wired: evidence now belongs to a source rather than a purchase, so a combined purchase offers one link per source. Three facts added to the read: quantity and unit apart, the budget line's name separately from its reference, and the capacity the certifier signed in, taken from the frozen assignment snapshot. A newer revision is announced but never substituted; a superseded version says read-only and keeps every value. 11 component + 3 server tests. Verified live as Amina. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G11 | Slice 2H — U13 publication evidence and recovery (14 artboards) per rule 6 | Partial | 2026-09-18, commit `0e4c4a85`. Four distinct status rows from a server-side projection; unknown is its own state and offers reconciliation rather than a blind retry; AO dispatch recording separated from technical retry/reconcile, with the responsible role named where a reader holds neither. Verified live as Amina. 8 component tests. **Owed:** the Treasury form and correction dialogs, withdrawal request/decision dialogs, fidelity assertions, browser spec. **Dialogs closed 2026-09-18, commit `46bff957`.** The screen had been emitting `record-treasury`/`correct-treasury` into a flag with no dialog behind it, and the withdrawal route had no UI at all despite both commands being built and tested. Recording asks the AO to confirm the document match, unchecked every time, with the missing piece named. Correction keeps the prior evidence visible, requires a reason and uses no overwrite language. Withdrawal is two dialogs for two people: the AO states a reason, the statutory authority reads it and cannot rewrite it; once a request is open the AO's action is gone and the screen names who it waits on. 14 component + 3 server tests. Browser spec green (G13b); fidelity assertions green (G13a). **Still owed:** live exercise — both dialogs need a plan at "approved, publication pending" or "publication failed", and the canonical world is deliberately published and active. |
| PLN22-G12 | Slice 2I — U14 progress + U16 correction requests (12 artboards) per rule 6 | Partial | 2026-09-18, commit `bf0545d5`. Both screens greenfield; the v1.12 active-plan screen and its forecast cascade dialog deleted. Progress shows planned, covered and stage only, with quantity and value always together and units never summed; coverage comes only from an authorised drawdown and a reversal removes it; owner actuals are per proceeding, and a proceeding with no owner evidence carries no dated table at all. No completion column, no forecast column, no date-change action. Corrections lead with the required change, keep ids in detail, carry one hold with the outstanding count, and keep the permanent scope restriction separate. Completion is offered only once a later version is Active, with the reason stated when it is not. Last forecast residues removed: `forecast_dates` left the published Requisition projection (no reader; pin updated on both sides), the forecast tier left the per-proceeding variance, the two dead cascade adapter entry points are gone. Two latent defects fixed: accepted sources all read "Direct requirement" because `need` was never selected, and an Active plan's approval/publication facts had no renderer. Verified live as Mercy — 1 Programme / KES 80,000,000 and 250 Each / KES 50,000,000, the hold rendering in its own purchase only, and a no-change close leaving "1 issue still needs attention"; probe data removed. 16 server tests, 22 component tests. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G13 | Slice 2J — C01–C04 Planning-side missing-setting panels (4 artboards) per rule 6 | Partial | 2026-09-18, commit `25686aab`. One shared panel behind all four variants, each placed at the action it blocks: approval authority at the AO's adoption, the closed submission window above the departmental submit (naming what stays permitted), and the method and schedule rules on the plan and the purchase editor, each naming its own purchase. A maintainer gets `/app/system-setup#<section>`; everyone else gets the ask-your-administrator sentence — no disabled setup control anywhere. A method the Planner has not chosen yet is deliberately not treated as a missing setting. Replaced the one-off method-issue sentence that offered its setup link to everyone, and retired `GovernanceTaskScreen`, a v1.12 remnant imported but unreachable since `ReviewScreen` took the governance decision. Verified live: with FY 2027/28 submissions closed, the panel rendered with all three labels and no control for Mercy, and resolved to the fiscal-years section for Administrator; the flag was restored immediately. 13 server tests, 5 component tests. Browser spec green (G13b); fidelity assertions green (G13a). |
| PLN22-G13a | The design-fidelity gate itself, rewritten for v1.23 | Done | 2026-09-18, commits `a0765009`, `70c54701`, `92864f04`, `7d8add5e`. **22 of 22 green** (`/tmp/claude-1002/fid5.log`). The gate had been comparing against v1.18 artboard files that no longer exist, so it could not have run. `openPanel`/`variantScope` index the v1.23 panels; one assertion per panel the fixture chain can reach, the rest named in their family's comment. It found five omissions no behaviour test could see: the plan-update row named neither the purchase it affects nor its reason (`change_reason` rendered but never selected); the departmental row put the financial year after the status; the Head of Department got the Author's card; the update fixture made no change at all; and U06 named who certified but not in what capacity. All fixed with tests. Of the last findings, none was a product gap: U07 hides Project name when blank exactly as §10.6 asks, so the gate takes up the control the artboard's Planner took up; U13's submission form and its correction are two artboards and now use two fixtures; U08-COMBINE could never render, because the keep-separate/combine choice needs more than one source and the workbench fixture has one (`reset_combinable_sources_fixture` supplies two); U12 clicked an evidence link without opening the purchase §10.10 says starts closed; U06 classified one of two requirements and then asked why acceptance was unavailable. Two artboards the specification has moved past carry named exemptions (§10.10's decision table, §10.13's Procurements started/Completion) that **fail as stale** once the pack is regenerated — which the gate proved by rejecting the U11-AO exemption, that artboard having already been refreshed. `onceEach` stops the instrument comparing a fixture's row count. FU-V123-01/05 carry both back to the design owner. |
| PLN22-G13b | The nine Planning browser specs green against the v1.23 build | Done | 2026-09-18, commits `4fe8e992`, `92864f04`, `eac025b8`, `6465c12a`. **54 tests, 0 failures** across `pln-workspace`, `pln-departmental`, `pln-annual-plan`, `pln-item`, `pln-finance`, `planning-evidence-pack`, `planning-governance`, `planning-publication`, `planning-release-evidence` (`/tmp/claude-1002/full1.log` 49/54, then the five repaired specs green in `core8`, `heavy1`, `heavy2`, `gov1`, `gov2`). `mode: "serial"` removed from every file so one failure no longer hides the rest, and `actionTimeout: 15_000` added so an unactionable click reports instead of eating a 180 s budget. Two product defects only a browser could reach: a failed publication showed the Accounting Officer no retry **and** no responsible role, because the role line was suppressed whenever the reader held any action at all (§10.13 requires it for exactly that reader); and the approval hand-off joined the notice, a middle dot and every Head of Procurement Function holder into one line (§10.6 asks for a notice and a separate Responsible person; §12.1 forbids delimiter-crammed facts). Both fixed with component tests proven against the old rule. Eleven browser assertions the specification had moved past were corrected to what §§10.3/10.4/10.6/10.10 actually say — `Included`/`Review details`, the Accountability section, the stage naming its authority, approval not activating, a row action being a link, the source reference and revision, and label/value adjacency. FU-V123-06 raised rather than fixed. |
| PLN22-G13c | Planning Python suite re-run after the v1.23 UI and read changes | Done | 2026-09-18. **19 modules, 311 tests, 0 failures** (`/tmp/claude-1002/pyplan.log`), run with no Playwright process active. Covers the `plan_read.waiting_on` shape change and the new `reset_combinable_sources_fixture`. Note for Phase 4: `bench run-tests --app kentender_procurement` as a whole still cannot discover, because `tender_management`'s tests import `kentender_procurement.tender_management.derived_models`, a package that does not exist. Pre-existing and unrelated — that tree was last touched by `b9c9afb2`/`12ab75e2`, long before this cycle — but it means the app-wide runner is unusable until that module is repaired or its tests retired. |
| PLN22-G14 | Phase 3: canonical seed green; §13.3 isolated profiles; every blank artboard value supplied; REQ + TPR stages re-run; persona browser pass | Partial | 2026-09-18, commit `3f5db2c7`. **The canonical seed works again** — it had been failing since the v1.18 rebuild. Five real faults fixed: profiles registered `Production verification pending` (the submission gate rejects it); the profile window started at the financial year while §10.2 anchors the schedules in May 2027, so no rule resolved; no reservation rule and no qualifying designation, so the mandatory allocation could not be assessed; the reset never purged the v1.18 publication chain and its filters keyed off an already-deleted plan, leaving two OCDS-shaped snapshots from the retired era to be reused; and the seed still drove the retired synchronous publication. `make seed-canonical THROUGH=planning` green, validates clean, `test_planning_seed` 7/7. **Owed:** the §13.3 isolated profiles, the blank artboard values, REQ/TPR stages, the persona pass. |
| PLN22-G15 | Phase 4 release evidence: full Planning regression; cross-module checkpoint; production build with changed hashes for `kentender_procurement` + `kentender_core`; 109 artboards compared at 1440 × 1024 and narrow; removed-construct scan; acceptance map closed truthfully; follow-ups and memory updated | Planned | — |

---

## Work register — Phase 0: Baseline and disposition

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-001 | Write this plan and tracker; retire the v1.18 plan/tracker into `retired/`; create `evidence/v1_22/` | Planned | — |
| PLN22-002 | Checkpoint-commit the uncommitted v1.18 Phase-3 UI work (PLN18-303..306 components, specs, Playwright specs) with a message naming it as superseded-on-landing (D3) | Planned | — |
| PLN22-003 | Record the baseline: `bench run-tests` counts for the 16 Planning test modules, one module per run; `npx vitest run --project procurement-planning`; Playwright not run (fixtures target the retired artboards); `bench migrate` clean | Planned | — |
| PLN22-004 | Generate `evidence/v1_22/FRAMES.md` from the 15 design files: 109 MVP artboard ids, no duplicates, as the fidelity/evidence filename list | Planned | — |
| PLN22-005 | Raise owner Q1 (C1, missing U06 artboards) and Q2 (C2, forecast/reminder acceptance rows); record answers in the decision log | Planned | — |
| PLN22-006 | Point `PLN-CHG-001_FOLLOW_UPS.md` at this cycle; add a v1.22 seam row to Budget, NDS, REQ and TPR follow-ups naming the classification-correction hold contract (§15.2 row "Scope-locked classification correction") | Planned | — |
| PLN22-007 | Diff the pack's `_ds/.../styles.css` against `kentender_core/.../kt_industry_tokens.css`; list any genuinely missing component class; confirm `ui-industry-design-gate` still passes (D12) | Planned | — |

---

## Work register — Phase 1: Domain delta

### 1A — Classification provenance and correction (§4.4, §5.1.6, §7.2; PLN21-AC-001..006)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-101 | `dpp_validation.accept_departmental_plan` accepts only `requirement_type_id` per proceeding entry; derives `procurement_category` from the effective governed catalogue entry; **rejects a client-supplied or mismatched category**; freezes both on the immutable decision | Planned | — |
| PLN22-102 | New doctype `DPP Classification Correction` with the seven §4.4 fields; immutable controller (no in-place edit, no delete); `supersedes_classification_evidence_id` chain | Planned | — |
| PLN22-103 | `services/dpp_classification.py`: `correct_accepted_requirement_classification` — one transaction rechecking accepted submission, current correction head, authority, catalogue mapping and every affected allocation; stale/concurrent attempts fail whole; new type must differ | Planned | — |
| PLN22-104 | Effective-classification projection used for new Planning work only; never rewrites an accepted decision, allocation, submitted Plan or Active Plan | Planned | — |
| PLN22-105 | `Plan Source Allocation` gains `classification_evidence`, `classification_requirement_type`, `classification_procurement_category`; patch existing rows from their acceptance evidence; a later correction never rewrites the stored snapshot | Planned | — |
| PLN22-106 | Affected-item recovery — the four outcomes: unallocated source becomes available corrected; mutable Draft item marked `Source correction required` (dissolve-and-re-form only); submitted/approved/Active Version unchanged and routed to correction or successor; scope-locked item records the correction, **holds new authorisation** and names the downstream owner route | Planned | — |
| PLN22-107 | Read `get_accepted_dpp_classification` — original acceptance, ordered correction history, current effective type/category, affected allocations, exact permitted correction/recovery action | Planned | — |
| PLN22-108 | Three new error codes `PLN_CLASSIFICATION_UNCHANGED`, `PLN_CLASSIFICATION_CORRECTION_STALE`, `PLN_CLASSIFICATION_CORRECTION_BLOCKED` with the exact §8 user text; reuse the existing `PLN_SOURCE_CORRECTION_REQUIRED` | Planned | — |
| PLN22-109 | `api.py`: expose `correct_accepted_requirement_classification` and `get_accepted_dpp_classification` with explicit signatures (no `**kwargs` transport-field trap) | Planned | — |
| PLN22-110 | `tests/test_dpp_classification_correction.py` — derivation; client category rejected; unchanged rejected; stale head rejected; excluded entry rejected; unauthorised rejected; each of the four recovery outcomes; concurrency; audit and export content | Planned | — |

### 1B — Forecast, cascade and reminder withdrawal (§7.5, §10.14, §11.9, §15.3; PLN22-AC-010, PLN23-AC-001)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-121 | Remove `preview_forecast_cascade` and `confirm_forecast_cascade` from `api.py`; keep the services, records and their tests green | Planned | — |
| PLN22-122 | Delete `ShiftScheduleDialog.vue` + spec; confirm no screen, route or label offers `Update expected dates` | Planned | — |
| PLN22-123 | Unregister every forecast/reminder runtime entry point: scheduler jobs in `hooks.py`, notification producers, setup controls. §7.5 now forbids the service entirely | Planned | — |
| PLN22-124 | Delete error codes `PLN_FORECAST_REASON_REQUIRED` and `PLN_CASCADE_INCLUDES_ACTUAL_MILESTONE` (removed from §8 by v1.23) | Planned | — |

### 1C — Residue removal and schema guard (D6)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-131 | Drop `exclusive_preference` from `Annual Plan Item` and from `plan_governance.py`'s copy list; patch | Planned | — |
| PLN22-132 | Drop the fourteen unused item-level `forecast_*` / `actual_*` date columns; confirm `Milestone Actual Event` is the only actual store and per-proceeding coverage reads from it | Planned | — |
| PLN22-133 | Confirm `plan_horizon` is a fixed literal with no editable selector and multi-year payloads are rejected server-side | Planned | — |
| PLN22-134 | Rename `test_planning_v118_schema` → `test_planning_v122_schema`; add the new prohibited strings from rule 3; **prove every guard with a planted violation** | Planned | — |

### 1D — Phase 1 exit

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-141 | `make planning-domain-gate` green | Planned | — |
| PLN22-142 | Three consecutive clean `bench migrate` | Planned | — |
| PLN22-143 | Cross-module checkpoint: Budget, NDS, Requisitions, Tender Preparation suites, one module per run, never alongside Playwright | Planned | — |

---

## Work register — Phase 2: UI slices

Each slice row set is: `a` read projection, `b` screen port, `c` vitest, `d` fidelity, `e` Playwright + live browser pass, `f` delete the superseded component. A slice closes on its gate, not on row `c`.

| ID | Slice | Families and artboards | Status | Evidence / gap |
|---|---|---|---|---|
| PLN22-201 | 2A | U01 (6) + U21 (16). One plain shortfall sentence and one recovery action on the workspace; Current plan resolves the Active pointer; empty `Your actions` omitted | Planned | — |
| PLN22-202 | 2B | U02–U05 (13). Inline funding beside the requirement; same-page HoD certification; explicit exclude/include with reason and cleared operative funding | Planned | — |
| PLN22-203 | 2C | U06 (8) incl. `U06-ACCEPTED-CLASSIFICATION` and `U06-CORRECT-CLASSIFICATION`. Requirement type is the only classification input; Category is derived read-only beside it | Planned | — |
| PLN22-204 | 2D | U07 (7) + U08 (4). Purchases lead, one concise Plan checks section, History secondary; no Approval/publication section on a Draft; `Send to Finance` absent while a check blocks | Planned | — |
| PLN22-205 | 2E | U09 (7). Six sections with `Supporting details` collapsed; omit `None`, `Not applicable`, `Single lot`, `Lot count 1` and plan-level reservation arithmetic | Planned | — |
| PLN22-206 | 2F | U10 (7). First view is Budget line, Approved, Planned, Difference, Result; availability and basis provenance are supporting detail | Planned | — |
| PLN22-207 | 2G | U11 (9) + U12 (4). Decision summary, visible issues, concise purchase rows, actor statement. **No purchase starts expanded.** Only header, prior accountability, statement and buttons vary by actor | Planned | — |
| PLN22-208 | 2H | U13 (14). Four distinct status rows; unknown is never rendered as failure; retry/reconcile only for a separately authorised technical operator | Planned | — |
| PLN22-209 | 2I | U14 (5) + U16 (7). Planned scope, authorised coverage, procurement stage; no completion placeholder. Corrections lead with the required change and the hold consequence | Planned | — |
| PLN22-210 | 2J | C01–C04 (4). Planning-side missing-setting panel only: Setting, Affected action, Responsible role, and an `Open System setup` link for an authorised maintainer | Planned | — |
| PLN22-211 | — | Delete the v1.12 remnants superseded by 2G/2H/2I: `ActivePlanScreen`, `PublicationResultScreen`, `GovernanceTaskScreen`, `ReviewScreen`, `SourceEvidenceScreen` and their specs, in their own slices | Planned | — |
| PLN22-212 | — | Retire the superseded Playwright specs (`planning-governance`, `planning-publication`, `planning-evidence-pack`, `planning-release-evidence`) as their replacements land | Planned | — |

---

## Work register — Phase 3: Seed and browser world

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-301 | Rebuild the §10.2 fixture under the frozen clock: 2 items, 3 sources, 2 departments, KES 130,000,000; BASE stays a **blocked** mandatory-allocation case (None/None, KES 48,000,000 shortfall) | Planned | — |
| PLN22-302 | READY as an explicitly labelled UI scenario only: laptop designation Youth, qualifying KES 50,000,000, 31.25% of the KES 160,000,000 annual budget | Planned | — |
| PLN22-303 | Supply the artboard values left blank (C4), one sub-row each: U04-EDIT saved direct reference; U05-ALL-EXCLUDED second exclusion reason; U06-STALE-SOURCE changed revision and value; U07-WAITING-FINANCE request instant; U07-UPDATE reason; U08-INCOMPATIBLE differing budget lines; U08-DUPLICATE cohort facts; U09-LOCKED requisition evidence; U09-CLASSIFICATION-LOCKED downstream record and route; U10 request/as-at instants; U11-COLLECTIVE recorder identity; U11-LATE-ADOPTION date and reason; U12 certification text; U13 attempt and activation instants; U14 proceeding ids; U16 accepted DPP update reference; U21-CANCEL-UPDATE reason | Planned | — |
| PLN22-304 | Isolated §13.3 presentation profiles, including the classification-correction history on DPP-MOH-DHI-2027-001 Submission 3 (Julia certifies 28 Nov 10:00, Mercy accepts Works/Works 29 Nov 15:00, item PPI-MOH-2027-044 forms 15:10, Mercy corrects to Non-consulting services/Services 30 Nov 09:20) — never mutations of the shared BASE records | Planned | — |
| PLN22-305 | Seed reset and rerun deterministic and idempotent; `make seed-canonical-validate` green twice | Planned | — |
| PLN22-306 | Re-run the Requisitions and Tender Preparation canonical stages on the new Plan | Planned | — |
| PLN22-307 | Persona browser pass as each §10.2 actor: Grace, Julia, Peter, Mercy, Charles, Josphat, Amina, Daniel, Naomi, plus a technical reader and a refused outsider | Planned | — |

---

## Work register — Phase 4: Release evidence

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN22-401 | Full Planning Python regression, one module per run | Planned | — |
| PLN22-402 | `npx vitest run --project procurement-planning` green | Planned | — |
| PLN22-403 | Every Planning Playwright spec + fidelity gate, single worker | Planned | — |
| PLN22-404 | Cross-module checkpoint: core, Budget, NDS, Requisitions, Tender Preparation | Planned | — |
| PLN22-405 | Production asset build via `./scripts/bench-with-node.sh build --app kentender_procurement` and `--app kentender_core`; record changed bundle hashes | Planned | — |
| PLN22-406 | All 111 MVP artboards compared at 1440 × 1024 and at a narrow width; screenshots in `evidence/v1_22/` | Planned | — |
| PLN22-407 | Removed-construct scan proving every rule-3 string absent from product code | Planned | — |
| PLN22-408 | Acceptance map below closed truthfully; §14.5 participant verification recorded separately as still owed | Planned | — |
| PLN22-409 | Follow-ups updated; memory updated | Planned | — |

---

## Acceptance map

Every row starts `Planned`. A row moves to `Done` only with a named test or an observed browser result on its own line. Rows the specification defers are marked `Future — excluded from the v1.22 MVP gate` and never counted as passes.

### Baseline acceptance set — §14.1, `PLN18-AC-001..134`

| Range | Coverage note | Status |
|---|---|---|
| AC-001..040 | Context, DPP lifecycle, formation, Finance, governance, publication, activation, scope, seeds | Planned |
| AC-041..080 | HOPF signature, collective evidence, AUTH scoping, reservation denominator, method eligibility, rule applicability, late adoption, publication package, Finance task uniqueness | Planned |
| AC-081..118, AC-120..123 | No-reservation invariant, affordability gates, statutory route, basis reuse, lotting, disposal absence, forbidden-state rendering, schedule rules, delivery boundary, baseline lock | Planned |
| **AC-119, AC-124..131** | **Future — excluded from the v1.23 MVP gate** (§14 preamble, `PLN23-CHG-001`) | Future |
| AC-132..134 | Profile-driven internal defaults; baseline card ordering; recompute before save | Planned |

### UX and state coverage — §14.2, `PLN18-UX-01..32`

| Range | Status |
|---|---|
| UX-01..19 | Planned |
| **UX-20, 21, 22** | **Future — excluded from the v1.23 MVP gate** |
| UX-23..32 | Planned |

### v1.19 usability acceptance — §14.4, `PLN19-UX-001..040`

| Range | Status |
|---|---|
| PLN19-UX-001..034 | Planned |
| **PLN19-UX-035** | **Future — excluded from the v1.23 MVP gate** |
| PLN19-UX-036..040 | Planned |

### Design-contract acceptance — §14.6, `PLN20-AC-001..012`

| ID | Status | Note |
|---|---|---|
| PLN20-AC-001..007 | Planned | — |
| PLN20-AC-008 | Planned | Depends on Phase 3 supplying every value the artboards left blank |
| PLN20-AC-009..012 | Planned | — |

### Classification provenance and correction — §14.7, `PLN21-AC-001..006`

| ID | Status | Note |
|---|---|---|
| PLN21-AC-001 | Planned | Phase 1A |
| PLN21-AC-002 | Planned | C1 closed — both artboards supplied in v1.23 |
| PLN21-AC-003..006 | Planned | Phase 1A + slice 2C |

### Simplicity and directness — §14.8, `PLN22-AC-001..013`

| ID | Status |
|---|---|
| PLN22-AC-001..009, 011..013 | Planned |
| PLN22-AC-010 | Planned — closes with PLN22-121..124 plus the removed-construct scan |

### v1.23 consistency acceptance — §14.9, `PLN23-AC-001..002`

| ID | Status | Note |
|---|---|---|
| PLN23-AC-001 | Planned | No forecast schema, route, API, U15 action, scheduler registration, reminder configuration or notification producer. Closes with PLN22-121..124 and the removed-construct scan |
| PLN23-AC-002 | Planned | Both U06 artboards reviewed and inventoried before Correct classification ships |

### Decision-specific regressions — §17.4

| Group | Count | Status |
|---|---|---|
| `PLN-RI-001..072` | 72 | Planned — carried from the v1.18 cycle; re-verified in this cycle's gates, not assumed. RI-030, RI-039 and RI-040 are **future-only** under v1.23 |
| `PLN-UX-001..020` | 20 | Planned |
| `PLN20-CHG-001..006` | 6 | Planned |
| `PLN21-CHG-001..003` | 3 | Planned |
| `PLN22-CHG-001..013` | 13 | Planned |
| `PLN23-CHG-001..002` | 2 | Planned |

### Critical end-to-end journeys — §14.3

| # | Journey | Status |
|---|---|---|
| 1 | Direct-only and mixed DPPs through ordinary governance | Planned |
| 2 | Racing first acceptances produce one APP and one Draft | Planned |
| 3 | Finance repeat review, concurrent Budget revision, Active reassessment | Planned |
| 4 | Mercy consolidates → Charles signs → Amina adopts → Daniel approves; segregation survives correction copies | Planned |
| 5 | Publication intent, Treasury gate, unknown/duplicate callbacks, withdrawal, published-held | Planned |
| 6 | Later Need cannot be absorbed into a scope-locked item; separate item succeeds | Planned |
| 7 | Two unresolved correction requests hold only the affected item | Planned |
| 8 | Two sequential proceedings retain distinct actuals; forecast comparison is a **future-facility** journey, excluded | Partial — forecast half excluded |
| 9 | Full authorised review and export; back-navigation restores context; every artboard state completed at the prescribed viewport | Planned |
