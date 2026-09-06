# Budget & Funding rebuild — implementation plan

**Authority:** `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_3.md` (the single implementation authority; this plan sequences work against it and adds no new requirements).
**Companions:** `02_BUD_Rebuild_Gap_Analysis.md` (what is wrong today), `IMPLEMENTATION_TRACKER.md` (phase status, evidence, decision log), `FOLLOW_UPS.md` (4 pre-existing open items this rebuild intersects).
**Status:** Phase 0 complete (gap analysis, this plan, tracker authored). Phases 1–10 not started.
**Author date:** 2026-09-04

## 1. Governing approach

Same workflow as Strategy's v1.6 correction pass and every other module rebuild this repo has done: research first, author plan + tracker, then execute phase by phase with the tracker's rows as the evidence ledger. No row is `Done` on inspection alone — each cites a command, test name, diff, or described screenshot.

Unlike Strategy's pass, **this is not a correction on top of same-day work** — `02_BUD_Rebuild_Gap_Analysis.md` confirms nothing in `kentender_budget` has been touched for v1.3 yet. Treat every phase below as real, unstarted scope, not a re-verification of claimed-done work.

v1.3's own posture governs disposition: **corrected in place, no alias, no redirect, no dual-read, no compatibility flag** (§1). Where this plan says "delete," the deletion lands in the same phase as its replacement — never deferred as future cleanup.

**Two structural departures from a naive phase-by-phase reading of the spec's own section order**, both made deliberately during planning research:

- The DocType rename (§17.1) is its own atomic phase (Phase 2), done first and alone, with no PE/FY/authorization semantics touched in the same pass. It is a first-of-its-kind operation in this repo (no prior `frappe.rename_doc` migration exists anywhere to crib from) and touches every layer of the app — bundling it with a second unrelated first-of-its-kind change (the authorization engine swap) would make every diff hunk ambiguous about which change it belongs to, and would compound two risky, novel operations into one unreviewable unit.
- PE/FY schema removal, the authorization rewrite, and the service-contract corrections are merged into one phase (Phase 4), not split — every one of the 15 service contracts calls into the same authorization scope checks being rewritten, so splitting "drop the PE gate from auth" and "drop the PE param from the contract that called it" across two phases doubles the review surface for what is really one coherent change viewed from two ends of the same call site.

## 2. Decision register (resolved 2026-09-04, recorded here and in the tracker's decision log)

| # | Decision | Resolution | Phase | Why it needs recording |
|---|---|---|---|---|
| D1 | ERPNext `Budget` DocType shim | **Scope in restoration.** `apps/erpnext/erpnext/accounts/doctype/budget/budget.json` was deleted (not merely uninstalled) by an earlier KenTender build claiming the "Budget" name; only a stub controller remains. Renaming KenTender's DocType (Phase 2) frees the name but does not restore ERPNext's own functionality. Restoring the real DocType is scoped as prerequisite work (Phase 3), not deferred as a documented deviation from BUD-AC-038. | 3 | The module owner explicitly chose full restoration over documenting a permanent deviation, given BUD-AC-038 and §17.2.1 both require ERPNext `Budget` to "remain fully functional" after this module installs — a literal reading this shim currently fails regardless of anything BUD-CHG-001 v1.3 itself changes. |
| D2 | KT-STD-001 §8.3 scope while touching the shared fixture register | **Strictly scope to Budget's own 3 required actors** (Naomi Chebet, reused from Strategy's own — never-applied — §14.1 claim; Josphat Mwangi; Beatrice Kamau). Do not also add Strategy's still-missing Esther Muthoni/Alfred Ochieng in the same pass. | 9 | Strategy's own gap is that module's unfinished business (already tracked, unresolved, in its own `IMPLEMENTATION_TRACKER.md`). Silently absorbing a second module's cross-doc debt into this change unit blurs ownership and scope; flagging it (as this plan and the gap analysis both now do) keeps the responsibility visible without taking it on. |
| D3 | Funding-source catalogue ownership (§19) | **Document as a cross-doc follow-up only.** Leave the `Funding Source` DocType where it is (`kentender_core`, already functioning); do not edit CFG-CHG-002 v0.6 within this change unit. | 9 | CFG-CHG-002 is not this app's document to edit, and the DocType already works correctly in production — the gap is purely one of documented ownership, not function. Mirrors how Strategy flagged its own out-of-ownership cross-doc gaps (`kentender_scope_map`'s shape mismatch) rather than editing another module's spec. |
| D4 | Doc naming/structure | **Mirror the now-established `02_`/`03_` + standalone gap analysis + separate `IMPLEMENTATION_TRACKER.md`/`FOLLOW_UPS.md` convention**, matching NDS, Planning and this week's Strategy pass — not Budget's own historical `01_Budget_Cleanup_*` naming from the v1.0 rebuild (deleted entirely in a prior legacy-cleanup commit, `d200ed4d`). `FOLLOW_UPS.md` already exists from the v1.2 rebuild and is retained, referenced, not re-authored. | 0 | Per-repo convention is to mirror the most current structurally-consistent sibling precedent for full-replacement change docs, not each module's own oldest lineage. |
| D5 | UI route-slug migration timing | **Not resolved yet — explicitly deferred to Phase 1's live route trace**, same posture as Strategy's own still-open route-architecture question (its tracker lists it `Planned`, not proven). Do not assume the DocType rename alone frees `/app/budget` safely — depends on whether Phase 3's restored ERPNext `Budget` DocType would also claim that slug. | 1 → 7 | Two first-of-their-kind operations (D1's ERPNext restoration, the DocType rename) both bear on whether the target route slug is actually free; guessing before both land risks sizing Phase 7 wrong. |
| D6 | `kentender_scope_map` registration | **Comply literally with §17.1.** Unlike Strategy's deviation, direct trace of `authorization.py`'s `scope_condition()`/`has_permission()` confirms registering is not a no-op for a site-wide role — a DocType absent from the map falls through to native DocPerm; one present with zero matching assignment rows returns a hard `1=0`. Budget is the mechanism's first production consumer anywhere in the codebase; size accordingly, with dedicated new test coverage, not a one-line sub-task. | 4 | The literal text is unambiguous here (unlike Strategy's case, where the map's own documented shape didn't match the real merge code) — and the mechanism has real, verified effect for a role like Budget's that has no existing precedent to defer to. |

## 3. Phase sequence

Each phase lists its exit condition. Detailed per-item rows live in `IMPLEMENTATION_TRACKER.md`.

### Phase 0 — Plan and tracker *(complete)*
Author `02_BUD_Rebuild_Gap_Analysis.md`, this plan, `IMPLEMENTATION_TRACKER.md`. Resolve D1–D6 with the module owner (D1–D3, D6 resolved outright; D5 explicitly deferred to Phase 1; D4 resolved by convention).

### Phase 1 — Repo-wide static research
Ground-truth pass before touching anything — this rebuild has no same-day precedent commit to lean on, so every claim in the gap analysis needs to hold under direct verification before phases are sized against it.

- Run the full disposed-concept grep across `kentender_budget` (and separately `kentender_procurement`/`kentender_core` for anything importing Budget): `procuring_entity`, non-`fiscal_year` `financial_year`, `Budget Viewer`, `Budget Reviewer`, `Budget Authority`, `Budget Activation Authority`, `budget-builder`, `budget-workbench`, `authorization_native`, `ResourceContext`.
- Feasibility research for D1 (ERPNext `Budget` restoration): determine how to reliably source the correct `budget.json`/`budget.py` (and any co-shipped test/report files) matching the installed erpnext version (16.10.1) — `apps/erpnext` has no usable git history in this bench, so this likely means a scratch `bench get-app`/pip-cache fetch of the matching release into an isolated location, not an in-place git restore. Document the exact sourcing method used, or the specific reason it can't be done, before Phase 3 starts.
- Confirm the `kentender_scope_map`/`ou_field` fallthrough semantics with a small, disposable proof (not just static reading) — verify a DocType absent from the map really does defer to native DocPerm, and one present with zero matching assignment rows really does return `1=0`, before Phase 4 commits to the D6 registration approach.
- Live route trace: does `/app/budget-funding/{id}[/tab]` etc. survive direct load, refresh, and browser back/forward with state intact today? This establishes the *baseline* Phase 7 must not regress, independent of the D5 slug-migration question.
- Confirm whether the contract service principal (Contract Management's caller for `convert_reservation`/`adjust_commitment`) is genuinely a service account today, not a business role — §7 requires this distinction hold.

**Exit:** a scan-results addendum to the gap analysis; D1's sourcing method (or its documented infeasibility) confirmed; every subsequent phase's scope corrected against these findings before being treated as accurately sized.

### Phase 2 — KenTender DocType rename (atomic, alone)
- Rename `Budget` → `Procurement Budget`, `Budget Version` → `Procurement Budget Version`, `Budget Line` → `Procurement Budget Line`, `Budget Line Version` → `Procurement Budget Line Version`, via `frappe.rename_doc` in a dedicated migration patch covering existing rows.
- Update every `frappe.get_doc/get_all/db.get_value/db.exists` string literal, every route/service/API/UI reference, every fixture and test, every DocPerm/Page/label reference to the new names.
- Touch **nothing else** in this phase — no PE/FY field changes, no authorization changes, no contract signature changes. This is a pure rename with identical behaviour under new names.

**Exit:** `bench migrate` clean; the entire pre-existing test suite passes unmodified in intent (only doctype-name strings changed) under the new names; `frappe.db.exists("DocType", "Budget")` is `False`.

### Phase 3 — ERPNext `Budget` DocType restoration (D1)
Only possible once Phase 2 frees the `Budget` name.

- Source the correct erpnext v16.10.1 `budget.json` and full (non-stub) `budget.py`, per Phase 1's sourcing-method finding, plus any co-shipped test/report/print-format files.
- Reinstate them in `apps/erpnext/erpnext/accounts/doctype/budget/`, removing the KenTender-authored compatibility shim and its explanatory comment entirely.
- Verify `bench migrate` installs the real doctype cleanly, that `validate_expense_against_budget`/`get_accumulated_monthly_budget` execute their real logic (not the no-op stub), and that nothing in `kentender_budget`'s newly-renamed `Procurement Budget` family collides with it.
- If Phase 1 could not reliably source the historical files: stop here, do not improvise a from-scratch reimplementation of ERPNext's own doctype, and re-raise to the user for a fresh decision rather than silently falling back to D1's rejected "document as deviation" option.

**Exit:** ERPNext's real `Budget` doctype installs and functions on this site; `apps/erpnext` carries no KenTender-authored shim comment; BUD-AC-038 is verifiable by direct test, not by written deviation.

### Phase 4 — PE/FY schema, authorization and service contracts (merged)
- Drop `procuring_entity` from `Procurement Budget` and every dependent parameter/filter/index/fixture/test.
- Rename `financial_year` → `fiscal_year` on `Procurement Budget`, repointed at ERPNext `Fiscal Year` (not KenTender's disposed `Financial Year` doctype).
- Add the BUD-BR-002 database-level partial unique index (one Procurement Budget, one Active Version, per Fiscal Year — no PE dimension).
- Rewrite `budget_authorization.py` mirroring `strategy_authorization.py`'s landed pattern: drop `authorization_native`/`ResourceContext`/capability-string constants/raw `User Permission` reads; adopt `authorise_record(user=, business_role=, organisation_unit="", purpose=)`; read no-self-approval from the `Budget Audit Event` trail (already the source of truth Budget's own old code reads for the same check — transplant the predicate, not the mechanism).
- Same rewrite for `budget_check_reserve_contracts.py`'s `_require_finance_capability`.
- Drop PE/FY params from all 15 contracts (`resolve_budget_context`, `check_funding`, `reserve_funding`, `revalidate_reservations`, `release_reservation`, `convert_reservation`, `adjust_commitment`, `get_funding_lineage`, `save_budget_version_draft`, `save_budget_lines_draft`, `submit_budget_version`, `return_budget_version`, `approve_budget_version`, `create_budget_successor_version`, `close_budget`).
- Build a Budget-owned FY-only read contract mirroring Strategy's `list_available_fiscal_years()` (`strategy_ui_contracts.py:623-636`) — same narrow `ignore_permissions=True` justification (Fiscal Year rows carry no business/scope data).
- Register the three roles as `scope_type = Site-wide` and remove `Budget Viewer` in `business_role_registry.py`; bump the stale `"BUD-CHG-001 v1.2 §7"` citations to v1.3.
- Register the renamed Budget DocTypes into `kentender_scope_map` through both hooks per D6, with dedicated new test coverage (no existing test to extend — this is genuinely new ground).
- Update `kentender_procurement`'s `budget_gateway.py` call sites and `test_gateway_contracts.py`'s pinned assertion in lockstep, following the already-landed Strategy precedent in the same file.

**Exit:** `bench migrate` clean; no Budget service accepts or returns a PE parameter; `budget_authorization.py` imports only `kentender_core.services.authorization`; the pinned cross-app contract test asserts `procuring_entity` is *absent* from `list_eligible_budget_lines`'s param set; a direct-route access test proves the new `kentender_scope_map` entry actually gates access (not just installs without error).

### Phase 5 — Role cleanup, the rest
- Remove `Budget Viewer` from all 7 DocType permission arrays + the `budget_funding` Page doctype.
- Remove `Budget Viewer` and the three already-v1.2-stale roles (`Budget Reviewer`, `Budget Authority`, `Budget Activation Authority`) from `kentender_procurement`'s `procurement_home_page.py` role allowlist.
- Clean `authorization_role_registry.py`'s dead capability→role mappings (`"budget.list"→"Budget Viewer"` etc.).
- Update seed user fixtures — remove `Budget Viewer` from any role tuple, touching **only** the `Budget Viewer` half of any combined `("Strategy Viewer", "Budget Viewer")` tuple; leave `Strategy Viewer` alone as Strategy's own separately-tracked, still-open violation.

**Exit:** zero `grep -rn "Budget Viewer\|Budget Reviewer\|Budget Authority\|Budget Activation Authority"` hits across `kentender_budget`, `kentender_core` seeds, and `kentender_procurement` outside tracker/decision-log prose; read access for the three site-wide roles (plus Auditor) still works via their own DocPerm read rows.

### Phase 6 — Seed correction
- Remove the Kisumu/`PE-CGKIS` baseline from `kentender_mvp_v1_portfolio.py` entirely (Budget/Version/Line/actors/approval-document reference).
- Fix the shared cross-PE isolation test outside `kentender_budget` (`kentender_core/kentender_core/tests/test_kentender_mvp_v1_seed_contract.py:146-164`) so it no longer depends on the removed Kisumu fixture constants.
- Verify seeded IDs still match §15.3 exactly under the Phase 2 rename.
- Seed all 3 required actors (Naomi Chebet, Josphat Mwangi, Beatrice Kamau) with real `User Responsibility Assignment` records, since none currently exist in any seed code — confirmed by direct grep, not assumed from the spec's "reused" claim.
- Seed the §15.5 isolated Finance/commitment profiles (`BUD-SC-FIN-SINGLE` through `BUD-SC-DUPLICATE-CORRELATION`) and the §15.6 artboard-only successor Version 2, both resettable and non-contaminating per §15.7.

**Exit:** default seed run twice produces no change on the second run; a missing-Fiscal-Year seed run fails with `BUDGET_CONFIG_MISSING` and creates nothing; every position in §15.4 matches exactly; no `PE-CGKIS` reference remains in Budget's own seed code.

### Phase 7 — UI rebuild
- Execute the route-slug migration per Phase 1/D5's finding — either adopt `/app/budget` literally (if Phase 3's restored ERPNext doctype doesn't reclaim that slug) or record why the deviation is required, with owner sign-off, same posture Strategy's D5 will eventually resolve to.
- Remove the Procuring Entity row/card from all 5 screens.
- Replace `WorkingContextPicker.vue`'s combined PE+FY resolution with a Budget-owned FY-only filter component, backed by Phase 4's new FY-only read contract — not the shared PE+FY composable.
- Set `showPeSwitcher: false` on Budget's `PageRail` mounts (a prop toggle on the shared component's existing API, not a rewrite of `PageRail.vue` itself, which other modules still use).
- Build/verify each of the 5 screens against the artboard set, excluding the 8 stale files that model the retired BUD-DES-12/13A screens.

**Exit:** no screen renders a Procuring Entity row, card, or selector; Financial Year renders as a local, resettable filter with no scope/access effect; a browser journey proves direct-load/refresh/back-forward survive on all 5 canonical routes with record ID and tab state intact.

### Phase 8 — Design-fidelity and test infrastructure
- Retire the 14 dead legacy Makefile targets (`ui-budget-funding-portfolio-gate` through `ui-budget-role-gate`) and their `.PHONY`/help-text entries.
- Build `tests/ui/smoke/design-fidelity/budget-fidelity.spec.ts` + `make ui-budget-fidelity-gate`, cloning the System-Setup reference implementation (`tests/ui/helpers/designFidelity.ts`).
- Close FOLLOW_UPS.md's FU-01 through FU-04 as they naturally fall out of Phase 2/5/7's route and role work — verify each with its own cited test run, not assumed closed by proximity.

**Exit:** the new fidelity gate passes against all 5 live routes plus the 4 BUD-DES-16 state variants; FOLLOW_UPS.md's register shows all 4 items closed with evidence; zero remaining `ui-budget-*-gate` targets reference a nonexistent spec, test module, or seed function.

### Phase 9 — Cross-doc corrections
- Add Naomi Chebet, Josphat Mwangi and Beatrice Kamau to KT-STD-001 §8.3 (D2's strict scope) — resolving the §8.4/§8.5 section-purpose collision first (§8.5 is currently "Units of measure," not a fixture-timeline register; either extend §8.4 "Fiscal years" or add a clearly-scoped new subsection, not silently repurpose §8.5's existing UOM content).
- Record the funding-source catalogue ownership gap (D3) as a flagged follow-up to CFG-CHG-002's owner — no edit to that document.

**Exit:** KT-STD-001 §8.3 carries exactly 3 new rows (no Strategy actors added); the fixture-instant/UOM section collision is resolved without content loss; the funding-source flag is recorded in the tracker, not silently dropped.

### Phase 10 — Acceptance mapping and release verification
- Map all 38 BUD-AC IDs to owning tests or live-verification evidence in the tracker, per §16.1's rule-coverage groups.
- Run the full `kentender_budget` suite, the cross-app contract suite (Procurement's `test_gateway_contracts.py` + the `kentender_core` shared seed-contract test), and the AUTH contract suite proving no Budget path reintroduces a `User Permission` read.
- Re-run Phase 1's static scan; confirm clean, including the erpnext-import scan (`grep -rn "from erpnext.accounts" kentender_budget` must return zero hits).
- Migration-on-a-real-data-copy check (§17.2.1) — install and migrate on a bench with ERPNext and HRMS present, asserting no DocType collision and that ERPNext `Budget` and `Cost Center` both function, per Phase 3's restoration.
- Explicit verification that BUD-AC-038 passes literally, closing D1 with test evidence rather than a recorded deviation.

**Exit:** every BUD-AC row has a cited test name or `bench console` evidence entry; `bench --site kentender.midas.com run-tests --app kentender_budget` green; both cross-app contract suites green; the static scan (including the erpnext-import check) clean.

## 4. Files in scope

**DocType JSON:** `kentender_budget/kentender_budget/kentender_budget/doctype/{budget,budget_version,budget_line,budget_line_version,funding_reservation,procurement_commitment,budget_audit_event}/*.json`.

**Page JSON:** `kentender_budget/kentender_budget/kentender_budget/page/budget_funding/budget_funding.json`.

**Out-of-app (Phase 3 only, D1):** `apps/erpnext/erpnext/accounts/doctype/budget/*` — flagged explicitly as outside `kentender_v1`'s normal ownership boundary.

**Services:** `services/budget_contracts.py`, `budget_line_contracts.py`, `budget_readiness_contracts.py`, `budget_check_reserve_contracts.py`, `budget_commitment_contracts.py`, `budget_downstream_contracts.py`, `budget_audit_contracts.py`, `budget_authorization.py`, `budget_permissions.py`, `budget_reference.py`.

**API:** `api/budget_api.py`, `api/dia_budget_control.py`.

**Patches:** new patch for the `frappe.rename_doc` migration (Phase 2); new patch for the PE/FY field drop + `fiscal_year` rename (Phase 4); new patch hard-deleting `Budget Viewer` (Phase 5).

**Vue/JS:** `public/js/budget_funding_page.js`, `budget_funding/Budget.vue`, `budget_funding/components/{BudgetWorkspaceScreen,BudgetVersionEditorScreen,BudgetDetailScreen,BudgetApprovalTaskScreen,BudgetLineDetailScreen}.vue`, `budget_funding/data/budgetApi.js`, `budget_shared/components/WorkingContextPicker.vue` (replace), `budget_shared/composables/useWorkingContext.js` (replace), `budget_shared/composables/useRouteState.js`, `usePageRail.js`.

**hooks.py / registry:** `kentender_budget/kentender_budget/hooks.py` (new `kentender_scope_map`/permission-hook entries); read-only-verify `kentender_core/kentender_core/public/js/kt_cl_surface_registry.js`, `kentender_core/kentender_core/hooks.py:268`.

**Cross-app (shared, touched in lockstep):** `kentender_core/kentender_core/services/business_role_registry.py`, `authorization_role_registry.py`; `kentender_core/kentender_core/seeds/kentender_mvp_v1/{constants,users}.py`; `kentender_core/kentender_core/tests/test_kentender_mvp_v1_seed_contract.py`; `kentender_core/kentender_core/public/js/kt_industry/components/PageRail.vue` (prop-toggle usage only, not the component itself); `kentender_procurement/.../procurement_planning/services/budget_gateway.py`, `tests/test_gateway_contracts.py`; `kentender_procurement/.../setup/procurement_home_page.py`; `kentender_procurement/.../patches/g013_ensure_strategy_budget_workspace_rows.py` (FU-01); `kentender_procurement/.../setup/workspace_permissions.py`, `public/js/procurement_sidebar_header.js`, `setup/tests/test_workspace_sidebar_fastpath.py` (FU-04); `kentender_budget/kentender_budget/patches/mvp1_teardown_drop_legacy_budget_doctypes.py`.

**Seeds:** `seeds/kentender_mvp_v1_portfolio.py`.

**Tests:** `tests/test_bud_chg_001_phase3_lifecycle.py`, `test_bud_chg_001_phase3_check_reserve.py` (extended as needed); new suites for the DocType rename, the `kentender_scope_map` registration, and the ERPNext restoration check.

**Design-fidelity / Makefile:** root `Makefile` (retire 14 dead targets, add `ui-budget-fidelity-gate`); new `tests/ui/smoke/design-fidelity/budget-fidelity.spec.ts`.

**Companion standards docs:** `docs/mvp-1-r1/09_unified_system_setup/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_1.md` (§8.3 addition, Phase 9; CFG-CHG-002 explicitly **not** edited, per D3).

## 5. Verification commands

```bash
# focused Python tests (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_budget \
  --module kentender_budget.tests.test_bud_chg_001_phase3_lifecycle
bench --site kentender.midas.com run-tests --app kentender_budget \
  --module kentender_budget.tests.test_bud_chg_001_phase3_check_reserve

# full app suite (Phase 10 release checkpoint)
bench --site kentender.midas.com run-tests --app kentender_budget

# cross-app contract pins (Phase 4, Phase 10)
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_planning.tests.test_gateway_contracts
bench --site kentender.midas.com run-tests --app kentender_core \
  --module kentender_core.tests.test_kentender_mvp_v1_seed_contract

# migration + rename verification (Phase 2, Phase 3, Phase 10)
bench --site kentender.midas.com migrate
bench --site kentender.midas.com console  # frappe.db.exists("DocType", "Budget") -> False; "Procurement Budget" -> True

# seed determinism (Phase 6)
bench --site kentender.midas.com execute kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_kentender_mvp_v1_portfolio
bench --site kentender.midas.com execute kentender_budget.seeds.kentender_mvp_v1_portfolio.upsert_kentender_mvp_v1_portfolio  # second run, expect no-op

# repository static scan (Phase 1, re-run Phase 10)
grep -rn "procuring_entity\|Budget Viewer\|Budget Reviewer\|Budget Authority\|Budget Activation Authority\|budget-builder\|budget-workbench\|authorization_native" \
  kentender_budget --include="*.py" --include="*.json" --include="*.js" --include="*.vue"
grep -rn "from erpnext.accounts" kentender_budget --include="*.py"

# assets (from apps/kentender_v1) — never plain `bench build`
cd /home/midasuser/frappe-bench && ./scripts/bench-with-node.sh build --app kentender_budget

# design-fidelity gate (Phase 8 — new target, cloning the System Setup reference implementation)
make ui-system-setup-fidelity-gate   # existing reference to clone
make ui-budget-fidelity-gate         # new target authored in Phase 8
```

Per `CLAUDE.md`: red/green on the focused node first, then the affected group, then the module suite once. Do not rerun the repository suite after each small fix. After CSS/JS changes, clear the site cache and hard-refresh Desk before diagnosing a code defect.

## 6. Non-goals

Restated from v1.3 §2 — this correction pass shall **not** reintroduce or half-build: appropriation, budget enactment, exchequer release, cash, ledger, invoice, payment or accounting workflows; any ERPNext accounting integration, Cost Center reference or reconciliation surface; Departmental Need approval or a reservation at Need acceptance; a separate Allocation record; Strategy fields; procurement category, method, schedule, lot, tender or contract authoring fields; actual expenditure, outstanding commitment or an `Unavailable` placeholder; forecasts, utilisation percentages, performance scores, trends or charts; manual reservation or commitment entry; a duplicate Finance task, decision or planner waiting screen; generic notes, descriptions, justification, contacts or miscellaneous attachments; editable technical identifiers; or a new Frappe shell, header, breadcrumb, global selector or navigation system.

Also explicitly out of scope per §18: do not use `owner_org_unit_id` as a user-scope or permission check (record eligibility only); do not create a Budget Viewer, Budget Reviewer or Budget Activation Authority role under any label; do not allow downstream raw SQL/ORM reads of Budget tables; do not permit client-only permission, total, floor, availability or lifecycle enforcement; do not permit direct edits of Active, Superseded or Closed data; do not rename the existing Budget or line identifiers (only the DocType names change, per §1.1's explicit "identifiers are deliberately unchanged").

## 7. Risks

**Cross-app blast radius:**
- `kentender_procurement`'s `budget_gateway.py` and its pinned `test_gateway_contracts.py` are the highest-certainty break point in Phase 4 — the test is designed to fail the moment `procuring_entity` is dropped from `list_eligible_budget_lines`. Treat the pin failure as expected and required, not a regression to investigate.
- Phase 6's Kisumu-seed removal breaks a **shared, `kentender_core`-owned** test (`test_kentender_mvp_v1_seed_contract.py`) that lives outside `kentender_budget` entirely — easy to miss if this phase is scoped as "Budget's own seed file only."
- Any phase touching `kentender_core.services.authorization`, `business_role_registry.py`, or `kentender_scope_map` (Phase 4) requires the cross-app AUTH contract suite to run at the release gate, not just Budget's own suite — and, being the mechanism's first production consumer, has no existing test to model new coverage on.

**Out-of-repo / novel-operation risk:**
- Phase 2's DocType rename and Phase 3's ERPNext restoration are both first-of-their-kind operations in this codebase, sequenced back to back with a hard dependency between them. Do not attempt to parallelize or reorder them — Phase 3 cannot start until Phase 2 frees the name.
- Phase 3 touches `apps/erpnext`, not `apps/kentender_v1` — outside this repo's normal ownership and review boundary. If Phase 1 cannot reliably source the correct historical files, stop and re-raise to the user rather than improvising a reconstruction of ERPNext's own doctype from scratch.

**In-repo:**
- Phase 7's PE/FY UI rework is materially larger than Strategy's equivalent gap: Strategy had no live combined-selector component to replace, only a display-layer PE row to remove. Budget's `WorkingContextPicker.vue`/`useWorkingContext.js` are threaded into every screen's data-loading path, not just its display — budget the phase accordingly, and verify via network trace (not just visual inspection) that no PE value crosses the wire even when not displayed.
- Phase 4's `kentender_scope_map` registration (D6) is genuinely new integration surface with no working precedent anywhere in the codebase to validate against — size its test coverage as new-feature work, not as "wire up an existing pattern."
- Phase 5's role cleanup touches `kentender_procurement`'s allowlist, which carries roles (`Budget Reviewer`, `Budget Authority`, `Budget Activation Authority`) that v1.2 itself already claimed to have removed — treat their continued presence there as evidence that a "confirmed removed per commit message" claim from any prior rebuild needs independent verification, not just citation.
