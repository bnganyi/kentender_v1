# Strategy Alignment rebuild — implementation plan

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_6.md` (the single implementation authority; this plan sequences work against it and adds no new requirements).
**Companions:** `02_STR_Rebuild_Gap_Analysis.md` (what is wrong today), `IMPLEMENTATION_TRACKER.md` (phase status, evidence, decision log), `FOLLOW_UPS.md` (deferred items, populated during implementation).
**Status:** Phase 0 complete (gap analysis, this plan, tracker authored). Phases 1–9 not started.
**Author date:** 2026-09-03

## 1. Governing approach

Same workflow as CFG-CHG-002 (PE/FY), Departmental Needs (NDS-CHG-001), Planning (PLN-CHG-001) and Budget (BUD-CHG-001): research first, author plan + tracker, then execute phase by phase with the tracker's rows as the evidence ledger. No row is `Done` on inspection alone — each cites a command, test name, diff, or described screenshot.

This is a **correction pass on top of same-day work**, not a rebuild from scratch. Commit `ccff1b80` (CU-3xx, 2026-09-03) already delivered the authorization-model migration this document's earlier drafts would otherwise have had to plan. Every phase below scopes only the gap `02_STR_Rebuild_Gap_Analysis.md` found still open — do not re-plan or re-verify-from-zero what that commit already landed; verify it once (Phase 1) and move on.

v1.6's own posture governs disposition: **corrected in place, no alias, no redirect, no dual-read, no compatibility flag** (§1). Where this plan says "delete," the deletion lands in the same phase as its replacement — never deferred as future cleanup.

## 2. Decision register (resolved 2026-09-03, recorded here and in the tracker's decision log)

| # | Decision | Resolution | Phase | Why it needs recording |
|---|---|---|---|---|
| D1 | `kentender_scope_map` registration for Strategy DocTypes | **Keep CU-302's non-registration.** No entry added. Documented as a deviation from §16.1's literal instruction. | 4 | §16.1 explicitly says to register; CU-3xx's commit message explicitly recorded a deliberate decision not to, because a site-wide role's predicate reduces to an assignment-existence check that DocPerm-via-URA-projection already provides, and because the ADR's own documented map shape doesn't match the real merge code in `kentender_core.services.authorization`. Flagged to the AUTH-ADR-001 owner as a possible spec erratum, not silently resolved either way. |
| D2 | `StrategyAuditEvent` (§4.6) — dedicated doctype vs. shared service | **Keep the shared `kentender_core.audit_event_service`.** No new doctype. Thread `decision.assignment.name` (the real URA record ID) into the event metadata to close the one genuine field gap. | 5 | A prior decision already rejected a bespoke doctype as duplicate mechanism (`strategy_audit.py:1-9`), and an existing test asserts its absence. Every other §4.6 field is already correctly threaded through the shared service — only the "exercised responsibility assignment ID" is wrong today (stored as a capability label, not the real assignment ID). |
| D3 | Dead two-PE seed text in `kentender_mvp_v1_strategy.py` | **Delete entirely**, not just leave the CU-307 stub. Rebuild the orphaned STR-DES v2 artboard-fixture generator off the live single-PE seed identity. | 5 | v1.6 §1 requires deletion "rather than aliased, redirected, dual-read or retained behind feature flags." The dead body is also a live trap: an unreachable function that would throw obscurely if ever called, rather than failing loudly. §14.4 still needs *some* mechanism for the isolated Version-2 fixture, so this is a rebuild, not a bare deletion. |
| D4 | Doc naming/structure for this v1.6 correction pass | **Mirror NDS/Planning exactly.** Restart Strategy's own doc numbering at `02_`/`03_` (the old `01_`-`04_` Cleanup/Rebuild lineage is fully superseded). Add a standalone gap-analysis doc (Strategy skipped this doc type last time). Use a separate `FOLLOW_UPS.md` rather than folding follow-ups into the tracker (Strategy's own immediate predecessor did fold them in; NDS/PLN's separate-file convention is more current). | 0 | Per repo convention, full-replacement change docs mirror sibling precedent's naming rather than inventing a new pattern per module. |
| D5 | UI route architecture (§10) | **Not resolved yet — explicitly deferred to Phase 1's own research.** Do not pre-commit to "no-op" or "single-Page consolidation" before that investigation lands; picking wrong wastes a full phase. | 1 → 6 | Whether the current three-Page Desk split satisfies §10's literal path-segment routes, or needs Departmental-Needs-style single-Page consolidation, is not decidable from spec text or code alone — it needs a live route trace (direct load / refresh / back-forward behaviour) first. |

## 3. Phase sequence

Each phase lists its exit condition. Detailed per-item rows live in `IMPLEMENTATION_TRACKER.md`.

### Phase 0 — Plan and tracker *(complete)*
Author `02_STR_Rebuild_Gap_Analysis.md`, this plan, `IMPLEMENTATION_TRACKER.md`, `FOLLOW_UPS.md` (skeleton). Resolve D1-D4 with the module owner; record D5 as explicitly deferred.

### Phase 1 — Repo-wide static verification and route-architecture research
Ground-truth pass before touching anything, since most of the "already done" claims in the gap analysis rest on a same-day commit that hasn't itself been re-verified independently.

- Run the full disposed-concept grep across `kentender_strategy` (and separately across `kentender_procurement`/`kentender_budget`/`kentender_core` for anything importing Strategy): `procuring_entity`, `owner_org_unit_id`, `FinancialYear` (the KenTender doctype, not ERPNext's), `STRATEGY_SCOPE_REQUIRED`, `STRATEGY_PERMISSION_DENIED`, `Strategy Reviewer`, `Strategy Approval Authority`, `Strategy Viewer`, and the retired lifecycle statuses (`In Review`, `Returned`, `Awaiting Approval`, `Approved`, `Archived` as plan-version statuses).
- Confirm or refute the missing STR-BR-004 database-level partial unique index (§16.1) by inspecting `patches/` and the `Strategic Plan Version` doctype's indexes.
- Confirm whether `Auditor` is a registered business-role-registry entry (per §6, "Auditor is a registered business role under AUTH-ADR-001 v1.6 §4.4, not a bare Frappe role") or still a bare Strategy DocPerm role.
- Trace a live render of `/app/strategy-portfolio` and `/app/strategy-plan-workspace/<id>` against §10's literal route table: does a direct load, refresh, or browser back/forward preserve the record ID and tab state? Decide — with the module owner, not by assumption — whether the existing three-Page split is an acceptable interpretation, or whether Departmental-Needs-style single-Page consolidation (`kt_cl_surface_registry.js:522-530` precedent) is required (D5).

**Exit:** a single scan-results table lands in an addendum to the gap analysis; every subsequent phase's scope is corrected against it before that phase is treated as accurately sized.

### Phase 2 — Schema correction
- Drop `procuring_entity_id` and `pe_fy_context` from `Strategic Plan` (currently hidden+read-only, not absent).
- Drop `owner_org_unit_id` from `Strategic Plan` (currently fully live).
- Rename `financial_year_id` → `fiscal_year` on `Performance Target` (Link options already point at ERPNext `Fiscal Year`; only the fieldname itself needs to move).
- Rewrite `_assert_no_primary_overlap()` (`strategy_transitions.py:98-130`) to drop the OU-partitioned overlap semantics and enforce STR-BR-004 exactly as written in v1.6 — no PE/OU qualifier, any two overlapping-date Primary plans conflict.
- Build the DB-level partial unique index guard if Phase 1 confirms it's missing.

**Exit:** `bench migrate` clean; `strategic_plan.json` field list carries no `procuring_entity_id`/`pe_fy_context`/`owner_org_unit_id`; `performance_target.json` carries `fiscal_year` not `financial_year_id`; existing lifecycle tests pass against the rewritten overlap function; a concurrent/bypass test proves the DB guard holds independent of the application check.

### Phase 3 — Service and command contract correction
- Rebuild `resolve_strategy_context()` to the literal §7/§8 shape: drop the `organisation_unit` param and its OU-keyed Supporting Framework filter entirely (site-wide — no OU dimension anywhere, not even for Supporting Frameworks); add a `fiscal_year` input alternative to the existing date input (exactly one of the two, per §7); add `include_supporting` (default `false`); strip `procuring_entity`/`organisation_unit` from the return payload.
- Update `api/strategy_consumer_api.py`'s wrapper to match — drop the dead `procuring_entity` passthrough kwarg described as a "transport-compat bridge."
- Verify `kentender_procurement`'s `strategy_gateway.py` call site and its pinned `test_gateway_contracts.py` are unaffected by the signature correction (it already calls with no args); update the pin only if it turns out to encode the old shape.

**Exit:** `resolve_strategy_context()` accepts exactly the §7 input shape and returns no PE/OU field; the pinned cross-app contract test still passes (or is corrected in this same phase, with a cross-reference note added for PLN-CHG-001's own tracker per §18).

### Phase 4 — Roles and permission cleanup
- Remove the `Strategy Viewer` Role's DocPerm rows from all five doctype JSONs and the Page/Workspace JSONs.
- Remove `ROLE_VIEWER`/its use from `strategy_permissions.py` and `UNRESTRICTED_READ_ROLES` in `strategy_ui_contracts.py`.
- Hard-delete the Role via a new patch, mirroring `str_chg_001_v1_7_delete_strategy_manager_role.py`.
- Remove any remaining `Strategy Viewer` seed pairing in `kentender_core`'s user seeds, confirming first (Phase 1) which seed path is actually executed.
- Record D1 (`kentender_scope_map` non-registration) in the tracker as a documented non-action, not silently.

**Exit:** zero `grep -rn "Strategy Viewer"` hits across `kentender_strategy` and `kentender_core` seeds outside tracker/decision-log prose; read access for the two site-wide roles still works via their own DocPerm read rows, matching §6 ("read access is not a third Strategy workflow role").

### Phase 5 — Dead code removal
- Extract the 4 genuinely-used functions out of `strategy_contracts.py` (`_node_ancestor_path`, `build_strategy_reference`, `list_active_targets`, `validate_strategy_reference`) into `strategy_consumer.py`, then delete `strategy_contracts.py` wholesale (~1,450 dead lines). Update the two test files that import from it.
- Delete the dead two-PE dataset text in `seeds/kentender_mvp_v1_strategy.py` (D3); rebuild `seed_str_des_v2_fixture()`/`teardown_str_des_v2_fixture()` keyed off the live single-PE seed identity.
- Thread `decision.assignment.name` into `strategy_audit.py::record_event()`'s metadata (D2), closing the one real §4.6 gap.
- Fix the stale `"STR-CHG-001 v1.5 §7"` citation at `business_role_registry.py:177-178` to `v1.6 §6`.

**Exit:** `strategy_contracts.py` no longer exists; `grep -rn "Strategic Outcome\|Strategy Value Commitment\|Performance Measurement" kentender_strategy` returns zero hits in executable code; the seed file carries no `PE-CGKIS`/`PE-MOH`/two-PE actor text; a working V2-fixture generator exists.

### Phase 6 — UI route architecture correction
Scoped entirely by Phase 1's D5 finding.

- If Phase 1 confirms the three-Page split cannot literally satisfy §10's routes: consolidate onto a single Frappe Page (Departmental-Needs-style), with `useRouteState.js`-style sub-route parsing distinguishing portfolio/plan/structure/approval.
- If Phase 1 confirms the current split is an accepted interpretation (owner sign-off recorded): this phase is a no-op, with the sign-off itself recorded as the evidence.
- Either way: verify back/forward/direct-load/refresh survive with filters, tab and selected record restored, per §12.1/§12.4.

**Exit:** owner-confirmed route architecture; a browser journey proves direct-load of each canonical route with a real record ID renders without a full page remount.

### Phase 7 — Artboard / design-fidelity verification
- Verify the new artboard set (`STR-DES-01..10.dc.html`, `Shell.dc.html`, `index.dc.html`) matches §11's exact content per screen. Resolve the CU-3xx commit's open item ("9 of 20 STR-DES artboards still depict the retired PE dimension") against the *new* set specifically — that note was written against the old, now-deleted 20-file set, so confirm rather than assume it's moot.
- Build a Strategy design-fidelity spec cloning the System Setup pattern (`tests/ui/helpers/designFidelity.ts` + a matching spec, from commit `9be512f3`) and a `make ui-strategy-fidelity-gate` target.
- Check whether the three legacy `ui-strategy-typography-gate`/`ui-strategy-alignment-ui-gate`/`ui-strategy-role-gate` Makefile targets reference now-deleted routes or artboards and need retirement.

**Exit:** the new fidelity gate passes against all 4 live routes plus the 4 STR-DES-10 state variants, using Phase 5's rebuilt V2-fixture generator for the Version-2 content shown in STR-DES-04..09.

### Phase 8 — Seed contract alignment
- Add the 3 Strategy actors (Esther Muthoni, Dr Alfred Ochieng, Naomi Chebet) and the 24-25 Nov 2026 fixture instant to KT-STD-001 §8.3/§8.5 (a required companion edit per v1.6 §18's document-correction table — touches the shared standard, not `kentender_strategy` app code).
- Verify/build the exact §14.3 MOH plan seed with its stable IDs.
- Verify the §14.2 fail-closed FY-2027-2028 check still resolves against the ERPNext `Fiscal Year` doctype.
- Verify the rebuilt V2 artboard fixture (Phase 5) produces exactly the §14.4 table's values.

**Exit:** default seed runs twice with identical results (STR-AC-023); a missing-FY seed run fails with `STRATEGY_CONFIG_MISSING` and creates nothing (STR-AC-024).

### Phase 9 — Acceptance-contract mapping and release verification
- Map all 34 STR-AC IDs to owning tests or live-verification evidence in the tracker, per §15.1's minimum rule-coverage groups.
- Run the full cross-app contract suite (Budget + Procurement Planning consumer tests, per §16.3) and the AUTH contract suite proving no Strategy path reintroduces a User Permission read.
- Execute §16.2's 12 minimum-coverage items explicitly — most already covered by the 7 existing suites, but re-verify against this pass's changes (especially the concurrent-overlap-with-command-bypass test, which now must exercise the Phase 2 DB-level guard rather than the removed OU-partitioned logic).
- Re-run Phase 1's static scan; confirm clean.

**Exit:** every STR-AC row has a cited test name or `bench console` evidence entry; `bench --site kentender.midas.com run-tests --app kentender_strategy` green; the cross-app gateway contract test green; the repo-wide static scan clean.

## 4. Files in scope

**DocType JSON:** `kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_plan/strategic_plan.json`, `.../doctype/strategic_plan_version/strategic_plan_version.json`, `.../doctype/strategy_node/strategy_node.json`, `.../doctype/performance_indicator/performance_indicator.json`, `.../doctype/performance_target/performance_target.json`.

**Page/Workspace JSON:** `.../page/strategy_portfolio/strategy_portfolio.json`, `.../page/strategy_plan_workspace/strategy_plan_workspace.json`, `.../page/strategy_review_task/strategy_review_task.json`, `.../workspace/strategy_management/strategy_management.json`.

**Services:** `services/strategy_authorization.py`, `strategy_consumer.py`, `strategy_contracts.py` (delete), `strategy_permissions.py`, `strategy_transitions.py`, `strategy_writes.py`, `strategy_readiness.py`, `strategy_domain_guards.py`, `strategy_reference.py`, `strategy_ui_contracts.py`, `strategy_audit.py`, `strategy_idempotency.py`.

**API:** `api/strategy_consumer_api.py`, `api/strategy_ui_api.py`.

**Patches:** existing `patches/cu_305_repoint_performance_target_fiscal_year.py`, `str_chg_001_v1_6_delete_retired_strategy_roles.py`, `str_chg_001_v1_7_delete_strategy_manager_role.py`; new patches for the PE/OU field drop + `fiscal_year` rename, and for the `Strategy Viewer` role deletion.

**Vue/JS:** `public/js/strategy_portfolio/StrategyPortfolio.vue`, `public/js/strategy_plan_workspace/StrategyPlanWorkspace.vue`, `public/js/strategy_plan_workspace/components/AddTargetDialog.vue`, `public/js/strategy_review_task/StrategyReviewTask.vue`, `public/js/strategy_shared/components/StructureTree.vue`, `public/js/strategy_shared/components/ConfirmDialog.vue`, `public/js/strategy_shared/composables/useRouteState.js`, `public/js/strategy_shared/data/frappeCall.js`.

**hooks.py / registry:** `kentender_strategy/kentender_strategy/hooks.py`; read-only-verify `kentender_core/kentender_core/public/js/kt_cl_surface_registry.js`.

**Seeds:** `seeds/kentender_mvp_v1_strategy.py`, `seeds/works_master_strategy_hierarchy.py` (read-only verify), `kentender_core/kentender_core/seeds/site_setup.py` (read-only verify).

**Cross-app (read-only unless Phase 3 forces a change):** `kentender_procurement/kentender_procurement/procurement_planning/services/strategy_gateway.py`, its `tests/test_gateway_contracts.py`.

**Tests:** `tests/test_str_chg_001_phase1_domain_model.py` through `phase7_ui_contracts.py` (7 files, extended as needed).

**Cross-app-owned, cited/cosmetic only:** `kentender_core/kentender_core/services/business_role_registry.py:177-178`.

**Companion standards doc:** `docs/mvp-1-r1/09_unified_system_setup/KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_1.md` (§8.3/§8.5 addition, Phase 8).

## 5. Verification commands

```bash
# focused Python tests (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase1_domain_model
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase2_lifecycle
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase3_governance
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase4_contracts
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase5_seed
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase6_consumers
bench --site kentender.midas.com run-tests --app kentender_strategy \
  --module kentender_strategy.tests.test_str_chg_001_phase7_ui_contracts

# full app suite (Phase 9 release checkpoint)
bench --site kentender.midas.com run-tests --app kentender_strategy

# cross-app contract pin (Phase 3, Phase 9)
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.procurement_planning.tests.test_gateway_contracts

# migration + seed determinism (Phase 2, Phase 8)
bench --site kentender.midas.com migrate
bench --site kentender.midas.com execute kentender_strategy.seeds.kentender_mvp_v1_strategy.upsert_kentender_mvp_v1_strategy
bench --site kentender.midas.com execute kentender_strategy.seeds.kentender_mvp_v1_strategy.upsert_kentender_mvp_v1_strategy  # second run, expect no-op

# repository static scan (Phase 1, re-run Phase 9)
grep -rn "procuring_entity\|owner_org_unit_id\|FinancialYear\|STRATEGY_SCOPE_REQUIRED\|STRATEGY_PERMISSION_DENIED\|Strategy Reviewer\|Strategy Approval Authority\|Strategy Viewer" \
  kentender_strategy --include="*.py" --include="*.json" --include="*.js" --include="*.vue"

# assets (from apps/kentender_v1) — never plain `bench build`
./scripts/bench-with-node.sh build --app kentender_strategy

# design-fidelity gate (Phase 7 — new target, cloning the System Setup reference implementation)
make ui-system-setup-fidelity-gate   # existing reference to clone
make ui-strategy-fidelity-gate       # new target authored in Phase 7
```

Per `CLAUDE.md`: red/green on the focused node first, then the affected group, then the module suite once. Do not rerun the repository suite after each small fix. After CSS/JS changes, clear the site cache and hard-refresh Desk before diagnosing a code defect.

## 6. Non-goals

Restated from v1.6 §2 — this correction pass shall **not** reintroduce or half-build: Public Value Objectives; Strategic Outcomes or an equivalent intermediate layer; treatment, remediation or corrective-action records; performance-result entry, verification or scoring; an advanced performance dashboard; requester-facing Strategy selection inside Departmental Needs; budget creation or confirmation; procurement method/schedule/lot/tender configuration; delivery, acceptance or contract-performance records; editable technical identifiers; source-reference, evidence, attachment or contact fields; generic notes/rationale/description fields with no defined consumer; baseline or tolerance fields; any duplicate of the Strategic Objective under another label; any new Frappe shell, page header, breadcrumb, global selector or navigation system.

Also explicitly out of scope per §17: no organisation-unit scope check/selector/column anywhere in a Strategy command, service or screen — this directly bears on Phase 2/3's field and logic removal, don't leave a shadow OU concept behind; no first-plan/first-year/Administrator fallback; no preference rule resolving ambiguous context; no downstream raw SQL/ORM read of Strategy tables from another app.

## 7. Risks

**Cross-app blast radius:**
- `kentender_procurement`'s `strategy_gateway.py` imports Strategy's consumer functions directly by Python import, not RPC. Phase 3's signature correction must be checked against `test_gateway_contracts.py`'s pinned assertions before being called Done.
- `kentender_budget` depends on the exact four functions (`list_active_targets`, `build_strategy_reference`, `validate_strategy_reference`, `_node_ancestor_path`) moving out of `strategy_contracts.py` in Phase 5 — Budget's `loadTargetOptions` UI control depends on them, and its `error:` callback resolves to an empty list rather than a visible failure, so a broken import path here fails silently on Budget's side. This is the single highest-risk file move in this plan.
- Any phase touching `kentender_core.services.authorization`, `business_role_registry.py`, or `audit_event_service.py` (Phase 4's role deletion, Phase 5's assignment-ID fix) requires the cross-app AUTH contract suite to run at the release gate per KT-STD-001/AUTH-ADR-001's shared-infrastructure rule, not just Strategy's own suite.

**In-repo:**
- Phase 2's rewrite of `_assert_no_primary_overlap()` changes real business behaviour (what counts as an overlap), not just schema. Needs its own explicit before/after test, not just "make the migration pass."
- Phase 6's size is genuinely unknown until Phase 1's route research lands — do not let the tracker pre-commit to "no-op" or "full consolidation" before that investigation completes.
- Phase 7 is a new build for Strategy, not a re-run of an existing gate — only System Setup has this machine-checked oracle today. Budget the phase accordingly.
