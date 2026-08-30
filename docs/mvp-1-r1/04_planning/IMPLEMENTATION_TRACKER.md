# PLN-CHG-001 v1.2 — Procurement Planning — tracker

**Authority:** `KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1.2.md`, approved by the Project Owner on 30 August 2026 (supersedes v1.1 in full).
**Companions:** `02_PLN_Rebuild_Gap_Analysis.md` (current-state facts and [confirm in Phase 0] rows), `03_PLN_Rebuild_Implementation_Plan.md` (decision register D1–D9, phase design, standing verification rules).
**Status:** Phase 0 closed 30 August 2026 (Project Owner approved full implementation the same day). Baseline recorded: 8 of 41 Python test modules OK (22 tests), 26 FAILED (dominant cause: deleted Demand doctype), 7 un-importable; the legacy workspace Playwright spec fails 14/14; the live `/app/procurement-planning` route 404s on `Plan Demand Allocation` behind a Workspace+redirect-shim chain. Dispositions for every existing file are in the gap analysis Appendix A; decisions D10/D11 fix the demolition phasing (model+services P1–P2, all Stitch UI P3, seeds detached P1 and rebuilt P11). Phase 1 closed 31 August 2026: the full §4 model is live (20 doctypes incl. the two new core catalogues), migrate is clean, composite uniques are enforced and probe-verified, the nine Demand-era doctypes and their tables are dropped, the server-side demolition (services/api/tests/seeds) is done, and two long-standing import-dead files (core users seed, journey_api) were repaired because they blocked the app's test runner. Phase 2 closed 31 August 2026: the full §5.1 DPP lifecycle with native §6 authorisation, the §8.2 envelope over a new command journal, the §9 error contract, replay-based Needs intake with a published-contract stale check, and the D6 Strategy/Budget gateways with signature drift alarms — 47 tests green incl. request-shaped endpoint coverage through frappe.handler (the NDS-914 class) with a planted-violation-proven **kwargs guard. DEBT-02 closed (native-only context eligibility); DEBT-01 (P11) open; PLN-203/PLN-208 carried into P6–P8 by design. Next: Phase 3 Slice A — workspace, context and the first Vue surface.
**Started:** 30 August 2026.
**Follow-ups:** `FOLLOW_UPS.md` does not exist yet — it is created at close (Budget variant: Register table up front, "Verifying a fix" section at the end). Items discovered mid-rebuild that are deliberately deferred are parked in the Carried debts table below until then.

## Tracker rules

1. Rows are permanent. Vocabulary: `Planned` / `In progress` / `Blocked` / `Done`. Reversed decisions are struck through in place, never deleted.
2. `Done` requires the row's **own** evidence in its Evidence cell — a command with its result counts, a named test, a diff, or a described browser observation with the literal rendered strings. "Looks right" is not evidence. Never record a result that was not actually observed.
3. A row that touches a file still referencing a spec-prohibited concept is not `Done`. Prohibited here: Demands (any import, doctype read or fixture), Value Commitment / `pvc_snapshot`, recommended method / method basis, lotting, contract-period/multi-year fields, preference/reservation scheme, actual-milestone entry, readiness score, capability store / Operational Scope Assignment / core `Workflow Task` for Planning decisions, Stitch markup or `kt-stitch-*` tokens, `kt_cl_surface_registry.js` entries for Planning, sidebar work-queue entries, browser-stored context as authority, legacy routes/aliases/dual-writes.
4. **Deletion lands in the same phase as its replacement.** "Delete later" is not a valid row state; the legacy surface a slice replaces dies inside that slice's phase.
5. §11 of the authority governs visual fidelity only. Implementing behaviour from artboard content instead of §12 is a defect. Screens are built from the `.dc.html` artboard's markup class-for-class, not from the prose spec or memory of sibling screens.
6. Slice gates (PLN-G03..G10) close only on browser evidence: per-role logins (each §6 actor the slice serves plus one out-of-scope actor), first paint **and** one interactive re-render, absence assertions on refusal paths, zero page-specific console errors. Component tests (D9) and request-shaped endpoint tests are gate conditions, not substitutes for this.
7. Static/architecture guards are `Done` only when verified by planting a violation.
8. Playwright spec files each own their own fixture Procuring Entity; fixture instants are pinned, never `now`-relative; fixture resets clear actor context preferences.
9. Diagnosis follows the §16.2 ladder; a full-suite run is never the first diagnostic step.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-08-30 | **D1** Rebuild in place per the §1.1 register; retain proven transactional mechanics as patterns; no Demand migration, alias or compatibility layer. | The register removes concepts (DPP replaces Demand-sourcing; six field families deleted); patching toward fewer concepts means holding two models at once. |
| 2026-08-30 | **D2** Desk Pages own the §10 route slugs; DocType names are chosen so their scrubbed slugs never collide (`Procurement Plan Item` already scrubs to the §10 route `procurement-plan-item`). Final names fixed by PLN-101. | A Page always loses to a same-named readable DocType's list view. NDS precedent: doctype `Departmental Need`, page `departmental-needs`. |
| 2026-08-30 | **D3** `/app/procurement-planning` ownership (existing Workspace fixture vs new Page) is settled empirically in Phase 0; the fixture is retired/renamed with a same-phase migrate run. | Workspace_sidebar JSON is reverse-synced by migrate; a dangling Workspace/Page link fails the whole-site migrate. |
| 2026-08-30 | **D4** Native Frappe Role / Workflow permission / User Permission only; module-local task doctypes, not core `Workflow Task`. | §6 prohibits a second permission store; core's task engine calls `require_capability()` internally (NDS D3 finding). Resolves the AUTH-ADR-001 `plan.*` dual-path BLOCKED finding by deleting the capability path. |
| 2026-08-30 | **D5** Needs is consumed only through `DepartmentalNeedAccepted.v2` / Superseded.v1 / Withdrawn.v1 (outbox drain) and the published read contracts; enforced by a bidirectional AST architecture test. | NDS D1 precedent; the AST test is the enforcement that held. |
| 2026-08-30 | **D6** Strategy/Budget are called through their published API modules via Planning adapter services named after the §8 spec verbs, recording the name deltas (`list_strategy_objectives`+`resolve_strategy_context`+`create_strategy_snapshot`; `list_eligible_budget_lines`; `check_funding`→token→`reserve_funding` within the 300 s TTL; `release_reservation` replacing the legacy `dia_budget_control` adapter; `revalidate_reservations`). Planning's current direct reads of Budget Line tables are closed. | The spec names are contract intents, not existing symbols; adapters keep spec vocabulary inside Planning while honouring the real published surface. |
| 2026-08-30 | **D7** Industry design system only; the NDS/Budget page-shell pattern (enterNative sidebar-only, cleared chrome host, hidden navbar/page-head, shared `kt_industry_page_rail.bundle.js`); no `kt_cl_surface_registry.js` entries; work queues via My Work provider + notification deep links, never sidebar entries. | Stitch/Civic Ledger are legacy debt; both the registry rule and the My Work rule are Project-Owner-settled (NDS FU-14). |
| 2026-08-30 | **D8** Playwright fixture endpoints live in seed/fixture modules invoked via `bench execute`, never in `api.py`. | ~900 of the old api.py's 1,463 lines are fixture endpoints in production code. |
| 2026-08-30 | **D9 (user decision)** §15.1(5) is satisfied literally: a Vue SFC vitest project (`@vitejs/plugin-vue` + jsdom — the repo's first) lands in Slice A; every later slice ships component tests alongside, not instead of, browser evidence. | Spec letter; the missing toolchain was a repo omission, not a decision. |
| 2026-08-30 | **D3 resolved (Phase 0).** The Workspace, not a Page, owns `/app/procurement-planning`; `planning_workspace_redirect.js` forwards it to the broken Stitch page. In P3 the Workspace fixture and shim are deleted and the new Desk Page claims the slug, with a same-phase migrate and a sidebar-JSON link check. | Observed in a real browser 2026-08-30 (PLN-006). |
| 2026-08-30 | **D10.** All six Stitch pages, their bind/fixture JS and `planning_workspace.css` are demolished together in **Phase 3**, not spread across slices A–F. | Tracker rule 4 ties deletion to replacement; the module-level replacement (new Planning page + workspace) lands in P3, and the old surfaces are already dead — nav parked at `coming-soon` since the Demands retirement, and the workspace 404s on `Plan Demand Allocation` (PLN-006). Their API layer disappears in P1–P2 regardless, so keeping them through P4–P8 would preserve broken dead code, not working behaviour. |
| 2026-08-30 | **D11.** Old planning services, api.py, tests and the doctype set are demolished in P1–P2 as the new model and services land; the old seeds are detached/import-cleaned in P1 (orchestrator's planning stage becomes a guarded no-op) and rebuilt in P11. | Rule 3: everything referencing dropped doctypes breaks at P1; carrying it further would leave prohibited-concept references in tree. `make seed-kentender-mvp-v1` must stay green between P1 and P11. |

## Headline findings (read before touching code)

1. The live module implements a superseded product: Demand-sourced consolidation, professional-review approval chain, Stitch UI, capability permissions. Its nav entry is parked at `coming-soon` (`setup/sidebar_availability.py:29-32`); its `api.py` was import-dead until CTX-CHG-001 Phase E. CTX-FU-03 (Demand-based Planning tests/Playwright) is closed by this rebuild.
2. The DPP aggregate (§4.1–§4.6) has no existing counterpart at all. `Plan Need Allocation` is the nearest thing and sits at the wrong layer.
3. Needs' side of §7.1 is **already done**: `DepartmentalNeedAccepted.v2` exists at exactly that version with exactly the six-facts payload; there was never a `.v1`. Superseded/Withdrawn are published but have **no consumer**; `NeedPlanningUsageChanged.v1` has a receiver (`project_need_planning_usage`) and **no publisher** — both are net-new Planning work.
4. Budget's reservation states already match §4.11 exactly (`Funding Reservation.status` incl. `Needs Attention`, `remaining_amount`, `plan_source_allocation` link). The gaps are on the Planning side: no `list_eligible_budget_lines` caller (direct table reads instead), release via the legacy `dia_budget_control` adapter (full-remainder only, synthetic idempotency key), no `revalidate_reservations` caller, reservation refs persisted onto the deleted `Demand Funding Allocation` doctype.
5. `check_funding` returns a token cached for **300 seconds**; `reserve_funding` consumes it all-or-none under row locks. The Finance confirmation command must be designed around that TTL.
6. The NDS retrospective's defect classes are standing gate conditions here (tracker rules 6–8): request-shaped endpoint tests (NDS-914), per-role browser logins (NDS-911/912), read-offer-vs-command assertions (NDS-807), seed-persona browser pass, pinned fixture instants, planted-violation guard proof.
7. Slug landmines: DocType `Procurement Plan Item` owns `procurement-plan-item` today; Workspace "Procurement Planning" relates to `/app/procurement-planning`; Page module "Procurement Planning" is a real Module Def, so 3-segment routes trigger Frappe's auto-sidebar swap (NDS boot-key/setup-skip mitigation applies).
8. `docs/mvp-1-r1/04_planning/design/` carries two `_ds` bundles; the PLN artboards reference `kentender-industry-82d82607-…`. The orphan is resolved in Phase 0.
9. **Test base class matters in this app:** deriving from legacy `frappe.tests.utils.FrappeTestCase` routes the runner through a compat preparation that imports *every* `test_*.py` in the whole app — so any stale import anywhere in kentender_procurement kills the run. Use `frappe.tests.IntegrationTestCase` (the NDS convention). Two such stale imports were fixed in Phase 1 (PLN-114); more may lurk in unrelated modules — fix them only when they block, and record each.
10. `frappe.delete_doc("DocType", …, force=True, delete_permanently=True)` does **not** reliably drop the backing table — `tabProcurement Plan` survived the doctype delete. Always follow with `drop table if exists` (the drop patch now does).

## Carried debts (must close before their named phase is Done)

| ID | Debt | Closes in | Detail |
|---|---|---|---|
| DEBT-01 | `kentender_core/seeds/kentender_mvp_v1/users.py` still assigns retired Demand/Planning persona roles (Requester, Business Approver, Planning Reviewer, Designated Approver, Tender Initiator, Planning Viewer, …) via local literals, and `ensure_demand_roles` keeps those Role docs creatable on fresh sites | 11 | Opened in Phase 1 (PLN-114). The file was import-dead before; the minimal fix restored importability without rewriting the Demand-era personas. The §14.2 persona rewrite in Phase 11 replaces the assignments and retires the literals. |
| ~~DEBT-02~~ | ~~`planning_context.py` still resolves PE eligibility through `user_scope_rows`~~ **Closed in Phase 2** (PLN-207): eligibility is now held-role + native PE User Permission; the scope-assignment read is deleted. | 2 | The AUTH-ADR-001 `plan.*` dual-path finding is now fully resolved: the capability path was deleted in P1 and the last scope-assignment read in P2. |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| PLN-G00 | Baseline & demolition survey recorded (exact non-passing test baseline; keep/correct/delete catalogue; caller grep; slug audit; `_ds` resolution; all [confirm in Phase 0] rows confirmed); no code changed | Done | 2026-08-30. PLN-001..009 all Done with row evidence; gap analysis Appendices A/B added; no product code changed (only the orphan design `_ds` bundle removed). Python baseline: 8/41 modules OK; Playwright: 14/14 workspace-spec failures; live route broken end-to-end. |
| PLN-G01 | §4 domain model migrated clean; uniqueness constraints for invariants 2/17/24 in place; old doctypes dropped by patch; absence guard planted-violation-proven | Done | 2026-08-30. 20 doctypes live (18 Planning + 2 core catalogues); `bench migrate` clean; 6 composite uniques verified against information_schema plus a live duplicate-root rejection; legacy doctypes **and tables** gone; schema suite Ran 6 OK with the token scan planted-violation-proven; seed orchestrator delegators verified as guarded no-ops. |
| PLN-G02 | §5 lifecycle services + §6 native permissions + §6.1 matrix + §9 errors + Needs drain + Strategy/Budget adapters green at service and handler layers | Done, with two rows deliberately carried | 2026-08-31. 47 Planning tests green across 6 modules (schema 6, context 3, lifecycle 20, validation 11, request-shaped 4, gateway drift 3) plus the NDS boundary suite (8). Carried by design: PLN-203 plan-side maker-checker pairs (→P8) and PLN-208 allocated-source event reactions (→P6) — both need objects their slices create. |
| PLN-G03 | Slice A (workspace & context) browser-verified per tracker rule 6; SFC vitest project running; My Work provider live; single nav entry | Planned | — |
| PLN-G04 | Slice B (DPP authoring) browser-verified: Author/HoD/acting-HoD journeys, window gating, certification, withdrawal/reopen | Planned | — |
| PLN-G05 | Slice C (DPP validation → auto Annual Plan) browser-verified; invariant-24 concurrency test green | Planned | — |
| PLN-G06 | Slice D (workbench/formation/Plan Item/dissolve) browser-verified incl. combined formation and source-correction marking | Planned | — |
| PLN-G07 | Slice E (Finance) browser-verified incl. shortfall; release/revalidate on the published Budget contracts; release-failure rollback proven | Planned | — |
| PLN-G08 | Slice F (governance) browser-verified: AO + statutory see the complete immutable Plan; correction chain restarts at AO; maker-checker planted-violation-proven | Planned | — |
| PLN-G09 | Slice G (publication/Active/successor) browser-verified: activation only on acknowledgement; retry path; `NeedPlanningUsageChanged.v1` published | Planned | — |
| PLN-G10 | Slice H (§7.4 projection + drawdown consumption) contract tests green | Planned | — |
| PLN-G11 | §14 seeds idempotent (reset + rerun twice) with validate green; §14-persona browser pass recorded | Planned | — |
| PLN-G12 | §15.1(6) journeys + one full regression + cross-module checkpoint + build with bundle-hash confirmation + §16.3 evidence pack + final demolition sweep + AC/§19 tables completed + FOLLOW_UPS.md authored | Planned | — |

## Work register — Phase 0: Baseline & demolition survey

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-001 | Record the exact non-passing Python baseline for `procurement_planning` (per-file pass/fail/error, incl. `test_planning_mvp_seed_contract.py`'s deleted-module import) | Done | 2026-08-30, per-module `bench --site kentender.midas.com run-tests --app kentender_procurement --module …` over all 41 test modules: **8 OK (22 tests)** — `test_get_plan_item_editor` 3, `test_planning_authorization_gate05` 2, `test_planning_chg016_layout` 2, `test_planning_context_ctx_chg_001` 3, `test_planning_mvp1_no_package_dual_write` 2, `test_planning_pe_scope_selection` 3, `test_planning_register_api` 6, `test_planning_rem009_absent` 1; **26 FAILED** — dominant error `Module import failed for Demand … No module named 'frappe.core.doctype.demand'` (18 modules), plus schema/layout failures in `test_planning_mvp1_schema` (2f+1e), `test_planning_ui_stitch_layout_guard` (3f+3e), `test_pp2_full_removal_abs` (1f), `test_planning_roles_exist` (2e), `test_support_plan_gate04` (1e), `test_planning_workspace_states` (5e), `test_planning_mvp_seed_contract` (0 ran, 1e); **7 un-importable** — `add_demand_to_plan` missing (`test_remove_plan_item`, 3 `test_scn_pln_*`), `demand_financial_year` missing (`test_planning_context_chg016`), two helpers no longer exported by `get_plan_item_editor` (`_funding_line_label`, `_attention_message`), `test_plan_need_allocation` no-run. A later phase is "no regression" only against this exact set minus what it deliberately fixes. |
| PLN-002 | Record the Playwright planning-suite baseline (expected: Demand-era failures) and the Makefile gates referencing deleted files | Done | 2026-08-30: `ui-planning-builder-gate` references deleted modules `test_list_eligible_demands`, `test_add_demand_to_plan_gate04` and deleted spec `planning-add-demand.spec.ts`; `planning-plan-update.spec.ts` also missing. Live-suite observation 2026-08-30: `npx playwright test tests/ui/smoke/planning/planning-workspace.spec.ts` → **14 failed / 14** (all PLN-UI-01 scenarios); with the live page broken (PLN-006), the Stitch suite is not a protectable baseline. |
| PLN-003 | Keep / correct-in-place / delete catalogue over all existing module files (~142), seeded from the gap analysis | Done | `02_PLN_Rebuild_Gap_Analysis.md` Appendix A: per-file/per-group dispositions with demolition phases (doctypes P1; services/api/tests P1–P2; all Stitch UI P3 — surfaces already dark; seeds P11 with guarded no-op through P1–P10; cross-app touch points listed). |
| PLN-004 | Repo-wide grep for external callers of planning services/API/doctypes (cross-app callers must not break silently) | Done | 2026-08-30 grep: live callers are kentender_core (`module_registry.py`, `kt_module_registry.js`, `authorization_role_registry.py` line 89 `procurement_planning.need_allocate`, seeds `planning/clear/validate/users/dev_full_reseed`, `test_desk_builder_layout_css.py`), procurement (`ensure_planning_roles.py`, `sidebar_availability.py`, workspace fastpath test, NDS architecture/events tests), root tests (`planningRoles.ts`, planning specs, `ui-smoke-rel-1610.spec.ts`, `stitch-desk-chrome.spec.ts`); archive/ references ignored. All catalogued in Appendix A "Outside the module". |
| PLN-005 | Slug-ownership audit: every §10 route slug vs existing Pages/DocTypes/Workspaces; record inputs for the D2 naming decision | Done | 2026-08-30: no DocType named `Departmental Procurement Plan`/`Annual Procurement Plan` exists (collisions would be created by naive §4 naming); DocType `Procurement Plan Item` owns `procurement-plan-item`; Pages are `planning-workspace` + five `procurement-plan-*`, none equal to a §10 slug; Workspace "Procurement Planning" relates to `/app/procurement-planning`. Gap analysis Appendix B. |
| PLN-006 | Empirically verify Page-vs-Workspace precedence for `/app/procurement-planning` (D3) and decide fixture retirement path | Done | 2026-08-30, Administrator in a real browser: `/app/procurement-planning` resolves to the Workspace and `planning_workspace_redirect.js` forwards to `/desk/planning-workspace`, which renders "Planning workspace could not be loaded … DocType Plan Demand Allocation not found" with a 404 on `api.get_planning_workspace`. Resolution: delete Workspace fixture + shim in P3, claim slug with the new Desk Page, same-phase migrate. |
| PLN-007 | Resolve the duplicate `design/_ds` bundles; confirm which bundle the 16 PLN artboards reference; remove the orphan | Done | `grep -ho '_ds/[a-z0-9-]*' design/*.dc.html \| sort -u` → only `kentender-industry-82d82607-…`; orphan `industry-f4215206-…` deleted 2026-08-30 (this phase's commit). |
| PLN-008 | Confirm every gap-analysis **[confirm in Phase 0]** row against the actual function bodies (item-version collapse, removal mechanics reuse, record-version uniformity, salvageable tests) | Done | Recorded in gap analysis Appendix B: record-version envelope pervasive (26 refs in api.py alone) — port, don't invent; predecessor used stable-item-root + version-spanning allocation lifecycle fields (`proposed_in_version`/`effective_from_version`/`reversed_by_version`) — PLN-101 recommendation recorded (single PlanItem doctype, stable public `plan_item_id` across successor copies, `(plan_version_id, plan_item_id)` unique); `remove_plan_item.py` downstream-check pattern reusable; salvageable tests named in Appendix A. |
| PLN-009 | Verify Needs outbox consumer semantics (`consume_events`/`acknowledge` ordering, per-consumer delivery) against its tests before designing the drain | Done | `departmental_needs/services/events.py`: `consume_events(consumer=, need=, after_sequence=)` ordered `departmental_need asc, sequence asc`, sequence taken under the Need's row lock, `acknowledge(consumer=, event_ids=)`; module docstring names Planning as the intended consumer. Drain design in P2 fits the contract unchanged. |

## Work register — Phase 1: Domain model

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-101 | Final DocType names (D2) with a scrub-check against every §10 route slug, recorded here before any JSON is written | Done | 2026-08-30. Names: Departmental Plan (+ Version/Entry/Submission/Submission Window/Validation Task/Validation Decision), Annual Plan (+ Version/Item/Publication/Publication Destination), Plan Source Allocation, Plan Finance Task/Decision, Plan Reservation Reference, Plan Governance Task/Decision; core catalogues Requirement Type + Procurement Method (new, module Kentender Core — §3 assigns them to Configuration & Governance and none existed). No scrubbed name equals a §10 route slug (`procurement-planning`, `departmental-procurement-plan`, `annual-procurement-plan`, `procurement-plan-item`); collision-check greps in Phase 0 evidence. Stable public ids (`plan_item_id` PPI-…, `allocation_id` PSA-…) are Data fields preserved across successor copies with `(plan_version, id)` composite uniques; row names are generated (`APIR-`/`PSAR-`). Money is `Currency` fields (Budget convention); currency displays from the Budget Line, never stored/edited (§4.4). |
| PLN-102 | DPPSubmissionWindow doctype (§4.1; states derived from clock, no manual status) | Done | `doctype/departmental_plan_submission_window/` — pe_fy_context unique; controller validates closes_at > opens_at; no title/status/reason fields. |
| PLN-103 | DPP root + DPPVersion + DPPEntry + DPPSubmission doctypes (§4.2–4.5) incl. one-root-per-PE/FY/OU uniqueness | Done | Four doctypes migrated; `pln_uniq_dpp_root (pe_fy_context, organisation_unit)` + `pln_uniq_dpp_version` composite uniques live (information_schema check in test); submission stores JSON entry snapshots + content hash + server-supplied attestation + authority snapshot; entry controller enforces shape only (completeness stays in the submit service — NDS FU-04 split noted in its docstring). |
| PLN-104 | DPPValidationTask + DPPValidationDecision (§4.6; classification on the decision, not the entry) | Done | Both migrated; task unique per submission with task_token + record_version; decision carries classifications/issues JSON, actor, authority snapshot, unique command_idempotency_key. |
| PLN-105 | AnnualProcurementPlan + PlanVersion (§4.7–4.8) incl. one-root-per-PE/FY and one-open-successor DB uniqueness (invariants 17/24) | Done | `Annual Plan.pe_fy_context` is `unique=1` (one root per context, invariant 24); `pln_uniq_plan_version (annual_plan, version_number)`; nine §4.8 version states incl. `Approved — publication pending`; `correction_of_plan_version` link present; submitted snapshot + hash fields for the immutable governance record. |
| PLN-106 | PlanItem + PlanSourceAllocation (§4.9–4.10; full-quantity allocation, one effective allocation per accepted entry) | Done | `pln_uniq_item_per_version`, `pln_uniq_alloc_per_version`, `pln_uniq_entry_per_version (plan_version, dpp_entry)` all live; item carries the seven planned dates, Objective lineage (objective + plan + plan version + display path), derived item/finance states; no quantity/value stored on the item (derived from allocations, invariant 10); allocation carries full source facts + five §4.10 states. |
| PLN-107 | FinanceTask + FinanceDecision + per-allocation reservation-reference rows (§4.11; no duplicated Budget position fields) | Done | Three doctypes migrated; task fixes source_set_hash + required amount + token; reservation reference links Budget's `Funding Reservation` and stores no Budget position/state fields (derived at read per §4.11); release reference/correlation fields for the §7.3 release evidence. |
| PLN-108 | PlanGovernanceTask + PlanDecision (§4.12; capacity, Board resolution reference) | Done | Both migrated; two-stage vocabulary only (AO adoption / Statutory approval); capacity recorded on task and decision; resolution_reference for Board approvals; unique idempotency key. |
| PLN-109 | PlanPublication (§4.13; attempt-numbered, destination-configured, four results) | Done | `Annual Plan Publication` + `Annual Plan Publication Destination` (governed destination_id/adapter, sandbox adapter as the sole option) migrated; payload_hash pins the exact approved payload; result Pending/Acknowledged/Failed/Indeterminate. |
| PLN-110 | Drop-old-doctypes patch (`pln_chg_001_v12_*`): the nine legacy doctypes and their rows; fresh-install migrate safety checked (Budget FU-01 class) | Done | `pln_chg_001_v12_drop_legacy_planning_doctypes` (pre_model_sync, existence-guarded) drops the 9 legacy doctypes **and their tables** (`delete_doc` alone left `tabProcurement Plan` behind — caught by the schema test, fixed with explicit `drop table if exists`); `pln_chg_001_v12_ensure_planning_roles` (pre) creates the §6 role set (Plan Statutory Approver + Planning Auditor were missing); `pln_chg_001_v12_planning_unique_indexes` (post) creates the composite uniques idempotently. Legacy `ensure_planning_roles` patch rewritten to a no-op (it imported the deleted `planning_permissions` at execute time — a fresh-install migrate breaker). `bench migrate` ran clean end-to-end. |
| PLN-111 | Schema tests: field allow-lists per §4 and §2.2; removed-concept absence guard (planted-violation-proven) | Done | `tests/test_planning_v12_schema.py` — 6 tests: exact field-set equality for all 20 doctypes, legacy doctypes AND tables absent, §1.1 token scan over doctype/services/seeds/tests/api.py (page/ excluded until D10's Phase 3 widens it), composite-index presence, live duplicate-root rejection, thin-controller ceiling. `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_planning.tests.test_planning_v12_schema` → Ran 6, OK. Planted violation (`pvc_snapshot` appended to seeds file) → FAILED (failures=1); removed → OK. |
| PLN-112 | Controllers stay thin (shape validation only); guard that business rules live in services | Done | Only 3 of 20 controllers validate (window instants, entry shape, item text bounds); the rest are pass-through; guard asserts ≤80 lines and no `.services` import per controller. |
| PLN-113 | **Added in Phase 1** — server demolition (D11): all Demand-era services (27 files), `api.py` fixture bulk, 40 test modules, 4 scenario seeds and `mvp1_constants.py` deleted; `seeds/kentender_mvp_v1.py` rewritten as honest stubs (`upsert_planning_base` → `PLN_CHG_001_V12_SEED_PENDING_PHASE_11`; `clear_planning_fixture_rows` clears the 18 v1.2 doctypes by namespace) | Done | `git rm` of doctype/services/tests/seeds; kept `planning_context.py` (corrected: capability import replaced by the §6 role set, `Procurement Plan` FY probe re-based onto `Annual Plan`), `planning_roles.py` (new), `test_planning_context_ctx_chg_001.py` (Ran 3, OK post-change). Core delegators verified live: `planning.upsert_planning` → `{"ok": false, "reason": "Procurement Plan DocType unavailable"}` (guarded no-op through P10); `clear_planning_fixture_rows` → 18 doctypes, 0 rows. |
| PLN-114 | **Added in Phase 1** — pre-existing cross-module import breakage fixed because it blocked the runner: `procurement_lifecycle/api/journey_api.py` imported the deleted `demand_planning_status` at module level (endpoint retired honestly with a `JOURNEY_DEMANDS_RETIRED` throw); `kentender_core/seeds/kentender_mvp_v1/users.py` imported the deleted `demands.services.demand_permissions` **and** `planning_permissions` (import-dead since the Demands retirement — replaced with local persona literals + the v1.2 role ensure; opens DEBT-01); dead `Plan Need Allocation` declaration stripped from `setup/departmental_needs_doctypes.py` (no callers repo-wide) | Done | Import matrix verified in bench console: users/clear/validate/api/planning_context/journey_api all import cleanly (`IMPORTS bad: []`); NDS architecture (Ran 8, OK) and events (Ran 18, OK) suites green after the boundary change. |

## Work register — Phase 2: Lifecycle + permissions core

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-201 | Command envelope: idempotency key + expected record version on every §8.2 command, rechecked in-transaction (port the proven NDS lifecycle pattern) | Done | `services/envelope.py` (token, payload fingerprint, journal replay/record, row-locked loads, record-version check + bump, task-token assert) over the new `Planning Command Journal` doctype (§8.2 needs an idempotency store for commands with no business decision record; Strategy precedent). Replay + key-reuse-with-different-payload + stale-version paths tested in `test_dpp_lifecycle` (Ran 20, OK). |
| PLN-202 | Native permission layer: §6 roles, PE/OU/Budget User Permission predicates, one scope predicate shared by lists, counts, details and commands | Done | `services/authority.py` — role + explicit PE/OU User Permission required (a role label alone grants nothing), masked not-found for record-addressed refusals, `authority_snapshot` on every decision, fail-closed context resolution. Out-of-scope actor and masked-refusal cases tested. FY is never a user assignment (§6); NDS's own viewer model differs (owner-author + FY rows), so the cross-module stale check runs as a system principal through the published contract — reasoned in `needs_intake.current_accepted_version_of`. |
| PLN-203 | §6.1 maker-checker matrix incl. correction-chain evidence tracking (`correction_of_plan_version_id` chains) | In progress | DPP pair enforced and tested (the HYBRID HoD+Planner persona is refused on their own submission with PLN_SEGREGATION_CONFLICT, and a different Planner then decides it). The plan-side pairs (planner↔finance↔AO↔statutory, correction chains) land with their commands in Phases 6–8; closes with PLN-806. |
| PLN-204 | §9 error contract (21 codes); unauthorised detail/task reads return not-found | Done | `errors.py` — closed 21-code set, `fail()` refuses invented codes (NDS pattern); `authority.not_found()` masks unauthorised reads as DoesNotExist. Exercised across the suites. |
| PLN-205 | §5.1 DPP lifecycle command services (open/save/submit/return/accept/update/withdraw/reopen) with window gating | Done | `services/dpp_lifecycle.py` + `services/dpp_validation.py`: all ten §5.1 rows. `test_dpp_lifecycle` (20) + `test_dpp_validation` (11) green: idempotent root, projection-once, eight-value direct entries, FY-bounded dates, funding eligibility, certification + server-side attestation (with the "FY " prefix the FY controller strips), window gating incl. post-close correction resubmission, withdraw/reopen, snapshot+task atomically, return→correction Draft with stable entry ids, accept→classifications on the decision + auto Annual Plan under the invariant-24 unique (concurrent loser reloads the winner). |
| PLN-206 | §5.2 Annual Plan lifecycle command services skeleton (auto-create on first acceptance through successor cancellation) | Done | `ensure_annual_plan` (root + Draft V1, UniqueValidationError→reuse) is live and tested (one root across two acceptances). The remaining §5.2 commands are each owned by their vertical slice (Phases 6–9) by design — see the phase table. |
| PLN-207 | Working-context integration: keep `planning_context.py` delegation; eligible-FY derivation via `offered=`; server-side preference only | Done | `planning_context.py` corrected: PE eligibility = held §6 role + native `User Permission` rows (`authority.permitted_pes`) — the scope-assignment read is gone (**closes DEBT-02**); FY probe re-based onto `Annual Plan`; CTX-CHG-001 delegation kept. `test_planning_context_ctx_chg_001` Ran 3, OK. |
| PLN-208 | Needs intake: outbox drain consumer + Need-origin projection + §7.1 successor/withdrawn reactions (stale refresh, Source correction required, governance block, Active-wait) | In progress | `services/needs_intake.py`: idempotent replay-based projection (add/refresh-facts-keep-funding/remove), coverage gaps, published-contract stale check — all tested. The event-drain reactions against *allocated* sources (Source correction required, governance block, Active-wait) need Plan Items to exist and land in Phase 6 (PLN-605); consuming/acknowledging outbox rows starts then so no event is acked before its reaction exists. |
| PLN-209 | Strategy adapter (D6): resolve context → list objectives → snapshot lineage on save; ineligible-objective blocking | Done | `services/strategy_gateway.py` over `resolve_strategy_context` → `primary_plan.id` → `list_strategy_objectives` (+ path display) and keyword-only `create_strategy_snapshot`; PLN_OBJECTIVE_INELIGIBLE on anything else. Signature drift alarm in `test_gateway_contracts` (Ran 3, OK); live exercise in Phase 6. |
| PLN-210 | Budget adapter (D6): eligible lines, check→token→reserve, release (batch correlation + idempotency), revalidate; direct table reads closed | Done | `services/budget_gateway.py`: spec-verb wrappers over the five published `budget_api` contracts (reserve_funding carries no actor — verified against source); release iterates the batch under one correlation, logs and raises PLN_RESERVATION_RELEASE_FAILED so the calling transition rolls back; `reservation_states` reads Budget's status without duplicating it. No Planning file reads Budget Line tables any more (the gateway import guard in `test_gateway_contracts` pins the allowed surfaces). Live reserve/release exercised in Phase 7. |
| PLN-211 | Request-shaped endpoint test harness through `frappe.handler` + `**kwargs`/`form_dict` AST guard (planted-violation-proven) | Done | `test_planning_api_requests` drives the full DPP journey and the return path through `frappe.handler.execute_cmd` with a populated form_dict (cmd + csrf_token, JSON-string payloads, string checkbox/version values) — Ran 4, OK. AST guard rejects any whitelisted `**kwargs` endpoint; proven by planting `def planted_violation(**kwargs)` → FAILED (failures=1) → removed → OK. |
| PLN-212 | Roles patch (§6 roles exist; retire the 10-role capability set); cancel/retire legacy Planning `Workflow Task` records | Done | Roles patch landed in P1; `pln_chg_001_v12_retire_legacy_planning_workflow_tasks` cancels open `plan.*` Workflow Tasks (state field is `state`, not `status` — corrected). Executed live: 0 open plan.* tasks remain. Legacy Role docs (Planning Reviewer et al.) stay until the P3 sweep confirms no remaining consumer. |
| PLN-213 | Bidirectional Planning↔Needs AST architecture test (D5) | Done | NDS's `test_departmental_needs_architecture` is the enforcement; updated for v1.2: `PLANNING_DOCTYPES` now lists the 18 new doctypes (reverse direction stays real) and `PUBLISHED_TO_PLANNING` adds `departmental_needs.errors` (a consumer cannot catch a contract's typed refusal without its exception type). It caught a real violation during this phase — `needs_intake` initially read `Departmental Need` directly and was rewritten onto `get_current_accepted_need` before the import was even flagged; the errors-module gap it then flagged was fixed as above. Ran 8, OK. |
| PLN-214 | **Added in Phase 2** — `tests/fixtures.py`: self-contained PLNT test world (own PE + two OUs, pinned far-future FYs, open + closed windows, catalogues, eight §6 personas incl. the HYBRID combined-assignment user, real link targets) with a PE-scoped cascade wipe for per-test isolation (namespace filtering alone missed API-created rows — the runner's rollback is deliberately not relied on) | Done | All suites run on it; §14 seed world untouched. |

## Work register — Phase 3: Slice A — Workspace & context

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-301 | Desk page shell on the D7 pattern (collision-checked slug, enterNative sidebar-only, cleared chrome host, hidden navbar/page-head, shared page rail, module-def sidebar-swap mitigation) | Planned | — |
| PLN-302 | Vue bundle + mount factory (globalProperties `__`/`frappe` before mount) + module CSS via `app_include_css` | Planned | — |
| PLN-303 | SFC vitest project (`procurement-planning`: @vitejs/plugin-vue + jsdom) with the first component's tests (D9) | Planned | — |
| PLN-304 | `ResolvePlanningContexts` + `GetPlanningWorkspace` read models (one scope predicate; role-aware queues; Pending addition + Not included rows) | Planned | — |
| PLN-305 | Workspace screen from PLN-DES-01 (context row with PE/FY selects, Your work, Departmental plans, window-closed message) ported class-for-class | Planned | — |
| PLN-306 | Common page states from PLN-DES-16 (no-context, empty, shortfall, publication-failed, load-error with support reference) | Planned | — |
| PLN-307 | My Work provider via `kt_my_work_providers`; retire core `_PRESENTATION` plan.* rows in the same change | Planned | — |
| PLN-308 | Navigation revival: single "Procurement Planning" entry; remove `sidebar_availability` parking, `planning_workspace_redirect.js`, the 7 stale `kt_cl_surface_registry.js` entries, and settle the Workspace fixture (D3) with a same-phase migrate | Planned | — |
| PLN-309 | Playwright spec on its own fixture PE: per-role logins (all seven §6 actors + no-context user), absence assertions, pinned instants | Planned | — |
| PLN-310 | Browser click-through evidence: first paint + interactive re-render (context switch), zero console errors | Planned | — |
| PLN-311 | Demolition: old `planning_workspace` page, its binds/fixtures and the workspace share of `planning_workspace.css` | Planned | — |

## Work register — Phase 4: Slice B — DPP authoring

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-401 | §8.2 DPP command endpoints with request-shaped tests (`OpenDepartmentalPlan`, `SaveNeedFunding`, `SaveDirectRequirement`, `RemoveDirectRequirement`, `SubmitDepartmentalPlan`) | Planned | — |
| PLN-402 | Departmental Plan screen from PLN-DES-02 (draft) and PLN-DES-05 (ready/certification/submit) | Planned | — |
| PLN-403 | Accepted-Need funding editor from PLN-DES-03 (six facts read-only; Budget Line + amount only; rejects Need-fact tampering) | Planned | — |
| PLN-404 | Direct requirement editor from PLN-DES-04 (exactly eight values; unit catalogue; FY-bounded required-by) | Planned | — |
| PLN-405 | Window gating incl. acting-HoD time-bound User Permission; server-supplied certification text; post-close resubmission rules | Planned | — |
| PLN-406 | Withdrawal / reopen-while-window-open flow (§5.1) | Planned | — |
| PLN-407 | Returned-correction Draft display: structured issues rendered next to their affected entries | Planned | — |
| PLN-408 | Component tests: field presence/absence, readiness notice, disabled submit, certification checkbox | Planned | — |
| PLN-409 | Playwright spec(s) on own PE: Author, HoD, acting-HoD (inside and outside the acting window), out-of-scope actor | Planned | — |
| PLN-410 | Browser click-through evidence incl. submit-blocked → funding-completed → submit-enabled re-render | Planned | — |
| PLN-411 | Demolition: legacy builder-era surfaces this slice supersedes | Planned | — |

## Work register — Phase 5: Slice C — DPP validation → auto Annual Plan

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-501 | `GetDPPValidationTask` + `ReturnDepartmentalPlan` + `AcceptDepartmentalPlan` endpoints (request-shaped tests) | Planned | — |
| PLN-502 | Validation screen from PLN-DES-06 (full immutable submission before controls; inline classification selects; certification card) | Planned | — |
| PLN-503 | Return dialog with structured issues (affected entry, problem, correction required) | Planned | — |
| PLN-504 | Acceptance transaction: classifications recorded on the decision; create/reuse Draft Annual Plan under the invariant-24 uniqueness constraint; concurrent-acceptance test proves one winner | Planned | — |
| PLN-505 | Pending-addition holding when the Plan Version is submitted/in governance; entries flow only to the later successor | Planned | — |
| PLN-506 | Component tests (decision controls, classification completeness, dialog copy) | Planned | — |
| PLN-507 | Playwright on own PE: Planner accept + return; maker-checker refusal for the HoD-submitter (absence-asserted) | Planned | — |
| PLN-508 | Browser click-through: acceptance lands the source in the workspace unallocated queue (interactive re-render) | Planned | — |

## Work register — Phase 6: Slice D — Workbench, formation, Plan Item

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-601 | `GetPlanVersion` read model + Annual Plan workbench screen from PLN-DES-07 (summary strip, unallocated sources, empty Plan Items state) | Planned | — |
| PLN-602 | `FormPlanItems` dialog from PLN-DES-08 (one-each / one-combined; compatibility checks; atomic idempotent formation; no blank item) | Planned | — |
| PLN-603 | Plan Item editor from PLN-DES-09 / PLN-DES-09A (allow-list fields only; combined title + aggregation reason; read-only derived rows) | Planned | — |
| PLN-604 | Strategic Objective selector on the live Strategy adapter (title + hierarchy path; ineligible-objective block; lineage snapshot on save) | Planned | — |
| PLN-605 | `DissolvePlanItem` (mutable Draft only; sources return to unallocated; confirmation copy) and **Source correction required** marking on DPP-successor acceptance | Planned | — |
| PLN-606 | Schedule + compatibility validation binding each failure to its exact control (§12.8) | Planned | — |
| PLN-607 | Component tests (formation dialog states, editor field allow-list, absent removed concepts) | Planned | — |
| PLN-608 | Playwright on own PE: single + combined formation, dissolve, incompatible-source refusal (absence-asserted) | Planned | — |
| PLN-609 | Browser click-through evidence incl. formation → editor → back-to-workbench re-renders | Planned | — |
| PLN-610 | Demolition: old builder/item-editor pages, binds, fixtures, their CSS share, and `preference_reservation.py` / `get_plan_implementation.py`-era services this slice supersedes | Planned | — |

## Work register — Phase 7: Slice E — Finance

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-701 | `RequestFinanceConfirmation` (full validation + create/reuse one current task) and `GetFinanceTask` (protected as-at positions via the Budget adapter) | Planned | — |
| PLN-702 | Finance screen from PLN-DES-10 + shortfall variant (Confirm omitted, deficient source shown, no partial reservation) | Planned | — |
| PLN-703 | `ConfirmFunding`: check→token→reserve within the 300 s TTL (server re-checks on expiry), all-or-none, decision + per-allocation reservation refs recorded | Planned | — |
| PLN-704 | `ReturnFromFinance` with required reason; planner-owned fields reopen | Planned | — |
| PLN-705 | Release migration off `dia_budget_control` onto `release_reservation` (batch correlation + idempotency key; unconverted remainder; release failure rolls back the Planning transition) | Planned | — |
| PLN-706 | `RevalidatePlanningReservations` caller + §4.11 stale rules (source-set/line/amount/currency changes flip Stale; narrative/Objective/schedule edits do not) | Planned | — |
| PLN-707 | Dissolve-with-effective-reservations atomicity (cancel task, release, mark allocations Released, return sources — or nothing) | Planned | — |
| PLN-708 | Component tests; Playwright on own PE with Budget Officer login (confirm + shortfall + return); browser click-through evidence | Planned | — |
| PLN-709 | Demolition: `plan_item_finance.py` Demand paths and the `Demand Funding Allocation` guarded writes | Planned | — |

## Work register — Phase 8: Slice F — Governance

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-801 | `SubmitConsolidatedPlan` (all sources allocated, items complete, Finance current; immutable snapshot + AO task) | Planned | — |
| PLN-802 | AO adoption task + screen from PLN-DES-11 (complete Plan table before controls; decision statement; adopt-and-submit) | Planned | — |
| PLN-803 | Statutory approval task + screen from PLN-DES-12 (route resolved from governed PE data; Board variant with mandatory resolution reference) | Planned | — |
| PLN-804 | Return dialogs from PLN-DES-15; `ReturnPlanVersion` creates the next numbered correction Draft linked via `correction_of_plan_version_id`, excluding pending additions | Planned | — |
| PLN-805 | `SubmitCorrectedPlan`: new snapshot, reservation revalidation, selective Finance repeat (only the §4.11 stale conditions), restart at AO adoption always | Planned | — |
| PLN-806 | Maker-checker across the evidence chain incl. corrections (planted-violation-proven) | Planned | — |
| PLN-807 | Component tests; Playwright on own PE with AO + statutory logins (adopt, approve, both returns); browser click-through evidence | Planned | — |
| PLN-808 | Demolition: `approve_plan_version.py`-era review chain, old review/approved pages + binds | Planned | — |

## Work register — Phase 9: Slice G — Publication, Active, successor

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-901 | Publication adapter (sandbox destination `MOH-APP-SANDBOX-v1` protocol) + `PublishAnnualPlan`: exact approved payload, activation only on acknowledgement, Failed/Indeterminate preserved, idempotent retry | Planned | — |
| PLN-902 | Publication result screen from PLN-DES-13 (read-only; retry visible to System Manager only) | Planned | — |
| PLN-903 | Active Annual Plan screen from PLN-DES-14 (summary strip, items with Requisition availability, adoption/approval/publication card, Prepare plan update) | Planned | — |
| PLN-904 | Successor lifecycle: `BeginPlanUpdate` (sole successor), `RemovePlanItemInSuccessor` (fresh downstream checks), `CancelPlanUpdate` (successor-only releases), supersession + removed-item release on acknowledgement | Planned | — |
| PLN-905 | `NeedPlanningUsageChanged.v1` publisher → `project_need_planning_usage`, fired only on Active begin/cease per accepted Need version | Planned | — |
| PLN-906 | Component tests; Playwright on own PE (activation, failed-publication retry, successor begin/cancel); browser click-through evidence | Planned | — |
| PLN-907 | Demolition: `Publication Event` doctype dir, `create_planning_handoff_snapshot.py`/`Planning Handoff Snapshot`, stale `procurement-plan-update` remnants | Planned | — |

## Work register — Phase 10: Slice H — Requisition eligibility

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-1001 | `GetRequisitionEligiblePlanItem.v2` projection: full §7.4 payload (lineage per allocation, expected operational result, balances, funding state, evaluation time); eligible only when Active + Finance current + positive remainders + no blocking successor | Planned | — |
| PLN-1002 | Drawdown-reference consumption: record/reverse authoritative Requisition drawdown references atomically against source-row and item balances; one-open-Requisition enforcement stays in the Requisitions module | Planned | — |
| PLN-1003 | Contract tests: eligible, each blocked state, sequential partial drawdowns, reversal, balance exhaustion | Planned | — |

## Work register — Phase 11: Seeds (§14)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-1101 | §14.1–14.3 prerequisite verification: fail loudly on any absent/differing PE, FY, OU, unit, catalogue, window, destination, actor, Objective or Budget Line; invent nothing | Planned | — |
| PLN-1102 | Integrated baseline (§14.4–14.6) driven through the real §8 commands with a frozen per-profile clock and the named role actors (never Administrator) | Planned | — |
| PLN-1103 | Isolated profiles: direct requirement (§14.7), combined sources (§14.8), return, shortfall, stale, successor, publication-failure — all outside the default baseline | Planned | — |
| PLN-1104 | KEBS profiles ×2 (§14.9: three accepted Needs; three direct entries) producing equivalent approved lineage | Planned | — |
| PLN-1105 | Orchestrator/validate/purge wiring: rewrite the planning stage delegator target, seed-validate checks, playwright purge; remove the dead demands-stage dependency for Planning rows | Planned | — |
| PLN-1106 | Seed reset + rerun twice: identical baseline, no duplicates (upsert by stable seed identifiers) | Planned | — |
| PLN-1107 | Browser pass logged in as the §14 personas (Grace, Peter, Julia inside her acting window, Mercy, Budget Officer, Amina, statutory approver, auditor, no-context) against the seeded site | Planned | — |

## Work register — Phase 12: Release verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| PLN-1201 | §15.1(6) integrated Playwright journeys: direct-only DPP, accepted-Need DPP, mixed DPP, integrated Active Plan, Finance shortfall, governance return, publication retry | Planned | — |
| PLN-1202 | One full module regression: Planning Python suite + `--project procurement-planning` vitest + Planning Playwright, run once at the end | Planned | — |
| PLN-1203 | Cross-module contract checkpoint: Needs, Strategy and Budget contract/architecture suites green after Planning's changes | Planned | — |
| PLN-1204 | Asset build via `./scripts/bench-with-node.sh build --app kentender_procurement` (+ kentender_core if touched); bundle content-hash change confirmed | Planned | — |
| PLN-1205 | §16.3 evidence pack: screenshots of all 16 PLN-DES artboard screens at 1440×1024; zero page-specific console errors and failed network requests | Planned | — |
| PLN-1206 | Final demolition sweep: `kt_cl_surface_registry.js`, Makefile planning gates, workspace/workspace_sidebar fixtures, removed-field audit over shipped schemas, no design-runtime files in production | Planned | — |
| PLN-1207 | AC map (below) and §19 conformance table completed with per-row evidence | Planned | — |
| PLN-1208 | `FOLLOW_UPS.md` authored (Budget variant) with everything deliberately left open; carried debts closed or moved there explicitly | Planned | — |
| PLN-1209 | Tracker Status paragraph updated to state exactly what was and was not run | Planned | — |

## Acceptance-criteria mapping (§15)

| AC | Criterion (abbrev.) | Phase | Status | Evidence |
|---|---|---|---|---|
| PLN-AC-001 | Zero/one/multiple PE+FY option cases fail closed | 3 | Planned | — |
| PLN-AC-002 | Workspace reads and direct routes create no record | 3 | Planned | — |
| PLN-AC-003 | One DPP root idempotently per PE/FY/OU | 4 | Planned | — |
| PLN-AC-004 | Accepted Need appears once, six read-only facts, no Needs-side Budget/Strategy/classification | 4 | Planned | — |
| PLN-AC-005 | Direct-only DPP submittable without any Need | 4 | Planned | — |
| PLN-AC-006 | Mixed DPP keeps distinct origins; no synthetic Need | 4 | Planned | — |
| PLN-AC-007 | Direct input limited to the eight values | 4 | Planned | — |
| PLN-AC-008 | Need-origin input limited to Budget Line + amount | 4 | Planned | — |
| PLN-AC-009 | Submission blocks missing Needs, partial quantities, incomplete funding, invalid dates, zero entries | 4 | Planned | — |
| PLN-AC-010 | HoD submission records exact certification; routes to validation, not AO | 4 | Planned | — |
| PLN-AC-011 | DPP return preserves submitted Version; entry-level correction | 5 | Planned | — |
| PLN-AC-012 | Acceptance requires classification; creates/reuses Draft Plan; no Plan Item created | 5 | Planned | — |
| PLN-AC-013 | No start gate / window-close wait / all-department gate / nil-plan declaration | 5 | Planned | — |
| PLN-AC-014 | Single and separate formation allocate once at full quantity | 6 | Planned | — |
| PLN-AC-015 | Combined formation rejects incompatible sources; aggregation reason required | 6 | Planned | — |
| PLN-AC-016 | No blank/source-less Plan Item | 6 | Planned | — |
| PLN-AC-017 | Exactly one eligible Active Objective; no Value Commitment | 6 | Planned | — |
| PLN-AC-018 | No contract period, lotting, recommended method, generic basis, actual milestones | 6 (schema: 1) | Planned | — |
| PLN-AC-019 | Seven planned dates required, chronological, required-by-bounded | 6 | Planned | — |
| PLN-AC-020 | Item value and funding breakdown equal source allocations | 6 | Planned | — |
| PLN-AC-021 | Finance data protected; current As-at position | 7 | Planned | — |
| PLN-AC-022 | Confirmation reserves all sources + one decision atomically, or none | 7 | Planned | — |
| PLN-AC-023 | Need acceptance, DPP actions, formation create no reservation | 7 | Planned | — |
| PLN-AC-024 | Stale only on source-set/line/amount/currency change or failed revalidation | 7 | Planned | — |
| PLN-AC-025 | AO and statutory tasks show the complete immutable Plan | 8 | Planned | — |
| PLN-AC-026 | AO adopts or returns the complete consolidated Plan | 8 | Planned | — |
| PLN-AC-027 | Exactly one statutory authority on the adopted Version | 8 | Planned | — |
| PLN-AC-028 | Every return: one actionable correction; snapshot preserved | 8 | Planned | — |
| PLN-AC-029 | Approval authorises the payload; does not activate | 9 | Planned | — |
| PLN-AC-030 | Publication activates only on acknowledgement | 9 | Planned | — |
| PLN-AC-031 | Failed/indeterminate publication retries same payload, no new approval | 9 | Planned | — |
| PLN-AC-032 | One Active Version; at most one open successor | 9 | Planned | — |
| PLN-AC-033 | Active predecessor eligibility unchanged until successor acknowledgement | 9 | Planned | — |
| PLN-AC-034 | Eligibility exposes remaining quantity/value; creates no Requisition | 10 | Planned | — |
| PLN-AC-035 | Active item removal blocked by drawdown/handoff/commitment/contract | 9 | Planned | — |
| PLN-AC-036 | No actual-milestone entry, Monitoring Officer, custom support workspace | 12 (schema: 1) | Planned | — |
| PLN-AC-037 | Same PE/FY/OU and task predicates everywhere | 2 | Planned | — |
| PLN-AC-038 | Same idempotency key → original result; concurrent commands → one winner | 2 | Planned | — |
| PLN-AC-039 | Cross-PE/FY/out-of-scope URLs disclose nothing | 12 (per slice) | Planned | — |
| PLN-AC-040 | Seed reset/rerun exact, duplicate-free | 11 | Planned | — |
| PLN-AC-041 | No HoPF/professional reviewer/committee/publication approver in the chain | 8 | Planned | — |
| PLN-AC-042 | Board approval records collective decision + resolution reference | 8 | Planned | — |
| PLN-AC-043 | Publication idempotent system action; retry reuses exact payload | 9 | Planned | — |
| PLN-AC-044 | Native Role/Workflow/User Permission only; no second store | 2 | Planned | — |
| PLN-AC-045 | Eligibility exposes every allocation + expected operational result + remainders | 10 | Planned | — |
| PLN-AC-046 | KEBS Needs-origin and direct profiles produce equivalent lineage | 11 | Planned | — |
| PLN-AC-047 | Draft item dissolvable; task cancelled, reservations released, sources reusable, history kept | 6 (reservations: 7) | Planned | — |
| PLN-AC-048 | Dissolution blocked after submission; atomic on release failure | 7 | Planned | — |
| PLN-AC-049 | Revalidation and releases use the Budget-owned service with correlation evidence | 7 | Planned | — |
| PLN-AC-050 | Correction preserves snapshot, excludes pending additions, restarts at AO | 8 | Planned | — |
| PLN-AC-051 | Finance repeats on correction only for defined stale conditions | 8 | Planned | — |
| PLN-AC-052 | DPP successor never rewrites an allocation; dissolve/re-form, return, or wait | 6 | Planned | — |
| PLN-AC-053 | Withdrawn initial DPP reopens only while the window is Open | 4 | Planned | — |
| PLN-AC-054 | Stranded accepted Needs show the exact not-included status; no bypass | 3 | Planned | — |
| PLN-AC-055 | Combined items reject different Budgets or currencies | 6 | Planned | — |
| PLN-AC-056 | Sequential Requisitions may draw while balances remain | 10 | Planned | — |
| PLN-AC-057 | Maker-checker blocks every prohibited pair; no unlisted approval level | 2 (per slice) | Planned | — |
| PLN-AC-058 | Concurrent first-DPP acceptance → one Annual Plan root, one open Version | 5 | Planned | — |
| PLN-AC-059 | One navigation entry; no role work-queue menu | 3 | Planned | — |
| PLN-AC-060 | Context server-authorised, visible, changeable; local storage never authority | 3 | Planned | — |
| PLN-AC-061 | Same generated Plan title on Draft/AO/statutory/Active; exact fixture row + total on governance surfaces | 12 | Planned | — |
| PLN-AC-062 | Combined fixture has deterministic required-by dates; completion satisfies both | 11 | Planned | — |

## §19 E2E-REQ-001 conformance check

| Non-drift control (E2E-REQ-001 §18) | Phase | Status | Evidence |
|---|---|---|---|
| 1. Structured system data is the authoritative record; attachments supporting only | 1–6 | Planned | — |
| 2. Business users complete fixed forms; no schema/manifest/template configuration | 4, 6 | Planned | — |
| 3. Code-owned first product; no generic configuration engine introduced | all | Planned | — |
| 4. Department data entered once, inherited via stable identifiers (`source_line_id` → `plan_item_line_id`) | 4–6, 10 | Planned | — |
| 5. Procurement adds only Procurement-owned rules; no silent rewrite of departmental facts | 4–6 | Planned | — |
| 6. Downstream responses/checks/obligations link to visible structured requirements | 10 | Planned | — |
| 7. Native Frappe permissions; AO adoption + exactly one statutory approval; no extra layers | 2, 8 | Planned | — |
| 8. New abstractions only after two released patterns prove the need | all | Planned | — |
