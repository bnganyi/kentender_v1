# Strategy Alignment rebuild — implementation plan

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.3.md` (the single implementation authority; this plan sequences work against it and adds no new requirements).
**Companion:** `IMPLEMENTATION_TRACKER.md` (phase-by-phase status, evidence, decision log).
**Status:** Phase 0 complete (this document + tracker authored). Phases 1–9 not started.
**Author date:** 2026-08-23

## 1. Governing approach

This rebuild follows the same workflow used for CFG-CHG-002 (PE and Financial Year Maintenance): research the existing app and its consumers before touching code, author a plan and a phased tracker, then execute phase by phase with the tracker's own rows as the evidence ledger. No phase is marked `Done` on inspection alone — each row cites a command, test name, or diff.

STR-CHG-001 v1.3's own instruction governs disposition of every existing concept: corrected in place, no alias, no redirect, no dual-read, no compatibility flag. Where this plan says "delete," the deletion happens in the same phase as the replacement lands — never as a separate future cleanup.

### 1.1 Two architecture decisions carried in from CFG-CHG-002 precedent

| Decision | Choice | Why |
|---|---|---|
| Authorization engine for the new Strategy Author/Reviewer/Approval Authority roles and their SoD enforcement | `kentender_core.services.authorization_policy` (Capability Profile + Operational Scope Assignment + Separation of Duties Rule) | Same engine CFG-CHG-002 adopted. Strategy's existing `org_scope_access.py`/`strategy_permissions.py` mechanism is the older of two parallel authorization mechanisms in this repo; CFG-CHG-002's own tracker flagged that split as debt worth reconciling. Using the same engine here starts that reconciliation instead of adding a third variant. |
| Audit trail | Delete the bespoke `Strategy Audit Event` doctype; call `kentender_core.services.audit_event_service.log_audit_event()` against core's generic `Audit Event` doctype, exactly as CFG-CHG-002 does for every PE/FY/Context transition | CFG-CHG-002's tracker explicitly named Strategy's bespoke audit mechanism as "a known, flagged issue, not a pattern to repeat." This rebuild is the opportunity to retire it rather than add a `correlation_id` field to a doctype the platform is already moving away from. |

## 2. What a prior cleanup pass already did (do not repeat)

`docs/mvp-1-r1/02_strategy/`'s three deleted-but-recoverable docs (`01_Strategy_Cleanup_Audit_Report.md`, `02_Strategy_Cleanup_Plan.md`, `03_Strategy_Cleanup_Tracker.md`, `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.0.md`) correspond to four real, merged commits (`190ab0a`, `05ccc36`, `8d1fc79`, `c78e7c2`). That v1.0 pass:

- fully deleted Public Value Objective (2 doctypes, 2 pages, rules engine) — confirmed absent from the current doctype list;
- fully deleted Strategy Corrective Action / treatment model — confirmed absent;
- renamed Plan Value Commitment → Strategy Value Commitment (v1.3 now requires deleting it outright, not renaming);
- added Strategic Objective/Outcome as distinct doctypes from Performance Indicator/Target;
- removed raw Administrator-identity fallback checks;
- implemented shapes close to the four §10 contracts inside `strategy_consumer.py`;
- hardened active-plan-overlap validation;
- audited (not force-rebuilt) the MoH/Kisumu seed.

It did **not** attempt: splitting `Strategic Plan` into `StrategicPlan`/`StrategicPlanVersion`; unifying Programme/Sub-programme/Objective/Outcome into one `StrategyNode`; deleting Strategy Value Commitment or Performance Measurement outright; renaming seed identifiers/actors to v1.3's exact scheme; whitelisting the four contracts as API endpoints; or the richer 8-state In-Review/Awaiting-Approval lifecycle. That remaining work is this plan's Phases 1–9.

## 3. Current-state inventory (from research, condensed)

12 doctypes, 13 pages, 11 services, 21 whitelisted API methods, 8 seed modules, 22 test files under `kentender_strategy/`. Full per-item verdicts (keep/delete/rebuild with reasoning) are recorded as the Phase 1 work-register items in the tracker rather than repeated here. Highlights that shape sequencing:

- `strategic_plan` conflates identity + version — the split is the Phase 1 spine everything else depends on.
- `strategy_programme`/`strategy_sub_programme`/`strategic_objective`/`strategic_outcome` unify into one new `StrategyNode` doctype. A doctype named "Strategy Node" existed once and was dropped by `patches/mvp1_teardown_drop_legacy_strategy_doctypes.py` in an earlier generation — this is a fresh build, not a revival; none of its old schema/logic survives to reuse.
- `strategy_portfolio_pilot` (Page + bundle + Vue root + `usePortfolio`/`useRouteState` composables + components + scoped token CSS) is the validated Vue-in-Desk-Page skeleton (AGENTS.md §6) to clone for every new screen, not reinvent.
- `strategy_consumer.py`'s contract functions are close to spec shape already but unreachable by RPC — `strategy_api.py` never imports them.

## 4. Downstream blast radius (must be sequenced, not discovered mid-build)

**`kentender_budget`** (live, real):
- `budget_line.py` → `strategy_consumer.apply_budget_primary_strategy_reference` (populates plain Data/Check fields on Budget Line, no Link field).
- `budget_reference.py` → `strategy_reference.pe_slug`.
- `budget_line_contracts.py` (XMOD-STR-001) → three `strategy_consumer` functions.
- Seeds/tests import `strategy_consumer` / seed hierarchy functions directly (`test_budget_line_strategy_validate.py`).
- `budget_readiness_contracts.py`/`budget_revision_contracts.py` contain user-facing copy naming "Strategy Value Commitment" — cosmetic, will read stale once the doctype is gone.

**`kentender_procurement`**:
- `procurement_lifecycle/strategy_alignment_handoff.py` already assumes an "Objective" vocabulary but is currently broken — it queries a doctype named `"Strategy Objective"` (doesn't exist; real name is `"Strategic Objective"`) with wrong field names (`objective_title`/`program`/`strategic_plan` instead of `title`/`programme`/`plan_version`). This is the natural landing spot for the new `list_strategy_objectives`/`create_strategy_snapshot` wiring, and its brokenness is pre-existing, not caused by this rebuild.
- `procurement_plan_item_version.json` carries `pvc_snapshot` (labelled "Strategy Value Commitment Snapshot") and `strategy_snapshot` fields whose producer function (`add_demand_to_plan.py::_strategy_snapshots`) was deleted in an unrelated commit and never recreated — these fields are already dead, independent of this rebuild, but `pvc_snapshot`'s name is schema debt referencing the doctype being deleted.
- Hard install dependency (`required_apps`) and seed-orchestration imports of `works_master_strategy_hierarchy` functions — naming-only coupling, not schema coupling.

**`kentender_core`**: seed orchestrator sequencing (`upsert_strategy` gates `upsert_budget`), `users.py` role-assignment import (`ensure_strategy_roles`), `stable_platform_seed` (imports `upsert_works_master_strategy_hierarchy` + named constants), Stitch Desk chrome registry rows for two Strategy pages, `test_module_registry.py`'s `page_js` enumeration.

**Playwright**: several specs assert on `kt-str-perf-*` / `kt-str-*commitments*` testids and on routes (`/desk/strategy-performance`, `/desk/strategy-value-commitments`, `/desk/strategy-plan-measurements`) that will not exist post-rebuild; Budget's cross-app specs seed Strategy fixtures directly via `bench execute kentender_strategy.seeds....`; `tests/ui/helpers/strategyWorkbench.ts` is already dead code (broken import, zero callers), unrelated to this rebuild.

**Zero references** in `kentender_suppliers`, `kentender_governance`, `kentender_compliance`, `kentender_stores`, `kentender_assets`, `kentender_integrations`, `kentender_transparency`.

## 5. Phase breakdown

Each phase below states its objective, primary surface touched, explicit deletions, and the STR-AC-0xx acceptance items it retires. Detailed per-item work-register rows live in the tracker.

### Phase 0 — Plan and tracker authored
This document + `IMPLEMENTATION_TRACKER.md`. No code touched.

### Phase 1 — Domain model rebuild
Split `strategic_plan` into `Strategic Plan` (identity: `plan_id`, `procuring_entity_id`, `owner_org_unit_id`, `title`, `plan_role`, `parent_primary_plan_id`, `period_start`, `period_end`) and `Strategic Plan Version` (approval boundary: `plan_version_id`, `plan_id`, `version_number`, `based_on_plan_version_id`, `status`, `effective_from`, `effective_to`, `return_reason`). Build new unified `Strategy Node` doctype (`strategy_node_id`, `plan_version_id`, `node_type`, `parent_node_id`, `title`, `display_order`) replacing `strategy_programme`/`strategy_sub_programme`/`strategic_objective`/`strategic_outcome`. Trim `Performance Indicator` (drop `measurement_frequency`/`data_source`/`responsible_function`; keep `definition`/`unit`; rename measured-node link to `measures_node_id`) and `Performance Target` (drop all baseline/tolerance/benefit_owner/measurement_verifier/period fields; keep `financial_year_id` XOR `target_by_date`, `comparison` restricted to 3 values, `target_value`). **Delete outright**: `Performance Measurement` doctype, `Strategy Value Commitment` + `Strategy Value Commitment Link` doctypes, `strategy_measurement.py` service, `strategy_performance.py` service, and their dedicated tests. Migrate audit trail: delete `Strategy Audit Event` doctype, route every transition through `audit_event_service.log_audit_event()`.
Retires: STR-AC-001, STR-AC-002, STR-AC-005, STR-AC-006, STR-AC-028.

### Phase 2 — Lifecycle engine
Rebuild `strategy_transitions.py` as a table-driven engine (modeled on `kentender_core/services/reference_data_transitions.py`) implementing the full 9-row §6.1 transition table (Draft→In Review→Returned→Awaiting Approval→Approved→Active→Superseded→Archived, including the Return branches). Implement `_check_expected_version()` optimistic concurrency (BR-016) exactly as CFG-CHG-002 did (document `modified` timestamp as the version token). Server-computes `available_actions` per version from current state + caller's actual capability (never a static status→action map). Atomic activate-supersede transaction (STR-BR-004/STR-AC-013/014) with a DB-level serialized overlap check.
Retires: STR-AC-010, STR-AC-011, STR-AC-012, STR-AC-013, STR-AC-014, STR-AC-015.

### Phase 3 — Roles and permissions
New Capability Profiles: Strategy Viewer, Strategy Author, Strategy Reviewer, Strategy Approval Authority, plus read-only capabilities for Budget/Finance Officer, Procurement Planner, Auditor (per §7). Operational Scope Assignments scoped by PE + optional OU + plan-role + effective dates, using the existing `resource_scope_type`/`resource_scope_id` dynamic-link pair on `Operational Scope Assignment` rather than a schema change. Separation of Duties Rule rows for each adjacent pair (submit↔review, submit↔approve, review↔approve); the 3-way non-repeat guarantee (author cannot both submit and approve the same version) additionally hand-checked via prior-capability membership in the transition functions, same pattern as CFG-CHG-002's context-reopen flow. `strategy_permissions.py` rewritten to call `authorization_policy.evaluate_capability`/`require_capability` instead of hand-rolled `can_*` checks; delete `can_submit_measurement`/`can_verify_measurement` (dead once measurement is gone).
Retires: STR-AC-003, STR-AC-004, STR-AC-010, STR-AC-021, STR-AC-022.

### Phase 4 — Service contracts (§10, §10.1)
Whitelist `resolve_strategy_context`, `list_strategy_objectives`, `get_strategy_lineage`, `create_strategy_snapshot` (new `api/strategy_consumer_api.py` or additions to `strategy_api.py` — decide at phase start) as thin wrappers over rebuilt `strategy_consumer.py` bodies. Implement the 8 §10.1 command contracts (`save_strategy_plan_draft`, `create_strategy_successor_version`, `save_strategy_structure_draft`, `submit_strategy_version`, `review_strategy_version`, `approve_strategy_version`, `activate_strategy_version`, `archive_strategy_version`) as thin dispatchers, following `reference_data_api.py`'s `dispatch: dict[str, Callable]` shape. New `Strategy Command Journal` doctype + idempotency wrapper modeled exactly on `reference_data_idempotency.py::run_idempotent()` for `create_strategy_snapshot`'s idempotent-on-correlation-ID requirement (BR-017/AC-019 equivalent). Implement the full §14 error contract (`STRATEGY_SCOPE_REQUIRED` … `STRATEGY_DOWNSTREAM_FORBIDDEN`).
Retires: STR-AC-009, STR-AC-016, STR-AC-017, STR-AC-018, STR-AC-019, STR-AC-020.

### Phase 5 — Seed contract (§16)
Rename actors to the exact 9 named users (`str.author.moh@example.test` … `str.auditor@example.test`); rebuild `STR-MOH-2023-001`/`STR-KSM-2023-001` with spec-exact stable node IDs (`PIL-MOH-2023-001` etc.) and exact lifecycle-authority timestamps. Validate PE/OU/FY prerequisites and fail closed with `STRATEGY_CONFIG_MISSING` rather than creating fallback records — build a thin Strategy-side existence guard (there is no ready-made bare PE/OU/FY resolver; `reference_data_resolver` only exposes a PE/FY-*Context*-scoped check) mirroring `create_context_draft`'s `PE_NOT_ACTIVE`/`FY_NOT_AVAILABLE` throw style. Keep the CFG-CHG-002 precedent of treating `PE-CGKIS` as the real docname and `PE-CGK` as spec shorthand. Delete dead seed shims (`moh_mvp_v1_strategy.py`, `works_master_strategy_purge.py`/`seed_works_master_strategy_purge.py` no-op stubs).
Retires: STR-AC-023, STR-AC-024.

### Phase 6 — Downstream consumer migration
Re-point `kentender_budget`'s `strategy_consumer` call sites at final contract shapes (function signatures may shift once Phase 1's schema lands); update its "Value Commitment" copy strings. Fix `kentender_procurement/procurement_lifecycle/strategy_alignment_handoff.py`'s broken doctype/field references and wire it to the new `list_strategy_objectives`/`create_strategy_snapshot` contracts (this is fixing Procurement's own consumer wiring to Strategy's published contract — in-boundary as a downstream-consumer fix, not a Strategy-internal change). Remove or relabel the dead `pvc_snapshot` field on `Procurement Plan Item Version` (its producer is already gone). Flag but do not silently fix: Playwright specs asserting on soon-to-be-removed testids/routes need updating in the same change window as their target screens disappear (Phase 7/8), not deferred indefinitely.
Retires: STR-AC-009 (downstream half).

### Phase 7 — Vue UI (STR-UI-01–04)
Clone `strategy_portfolio_pilot`'s Page/bundle/composable/component skeleton for the four canonical routes (`/app/strategy`, `/app/strategy/plan/{plan_id}`, `/app/strategy/plan/{plan_id}/version/{version_number}/structure`, `/app/strategy/review/{plan_version_id}`). Reuse `kt_industry_tokens.css`'s shared `--kt-*` tokens and `.kt-*` component classes rather than porting a second per-module token set the way the pilot's own `styles/tokens.css` did as a pilot-only stopgap. Route-state composable follows `useRouteState.js`'s active-flag mitigation for `frappe.router.off()`'s confirmed no-op. In-Vue confirm dialogs for Return/Approve/Activate per AGENTS.md §6.3. Build against the 12 Claude Design artboards already in `docs/mvp-1-r1/02_strategy/strategy_design/` (STR-DES-01 through STR-DES-12d) as the exact content/layout target — §12 is design-only, never a source of behavior.
Retires: STR-AC-025, STR-AC-026, STR-AC-027, STR-AC-029, STR-AC-030.

### Phase 8 — Shell/registry + module menu
Register the 4 routes in `kt_cl_surface_registry.js`; delete the legacy `strategy_alignment_shell.js`/`strategy_alignment_workspace_redirect.js` glue (superseded by the Vue route-state composable). Trim the Strategy Alignment module menu to exactly **Strategy Portfolio** and **Review tasks** (the latter visible only to an assigned Reviewer/Approval Authority) per §11 — no PVO/treatment/corrective-action/performance-management navigation survives. Delete the 13 legacy pages per the Phase 1 inventory verdicts, keeping only `strategy_portfolio_pilot`'s pattern (folded into the real STR-UI-01 build, not kept as a separate pilot page).

### Phase 9 — Verification against §17 acceptance contract
Full STR-AC-001…030 → owning-test mapping table, same discipline as CFG-CHG-002's Phase 9 (no AC left unassigned). Service/domain tests first (TDD red→green), then API/permission tests, then UI. State plainly, as CFG-CHG-002's tracker did, which layers are service/API-verified vs. which require live-browser verification if no browser tool is available in the executing session — carried forward as an explicit gap, never silently claimed done.

## 6. Test-and-verification discipline

Per AGENTS.md §7–8 and STR-CHG-001 §18.2: TDD per phase (smallest failing test → smallest passing change → refactor), focused-test reruns during a phase, one `kentender_strategy` full-suite run per phase group (not per edit), cross-module contract tests (Budget) only when a public Strategy contract shape actually changes, and one browser smoke pass per role at the release-candidate checkpoint (Author/Reviewer/Approval Authority/Viewer/forbidden actor), matching the exact 5 flows listed in spec §18.2.

## 7. Non-goals (explicitly out of scope, per spec §2.1/§19)

No Public Value Objective, treatment, corrective-action, or performance-result concept revived under a new label; no alias/compatibility/dual-read for anything deleted; no first-PE/first-OU/first-FY/first-plan/Administrator fallback; no client-only permission/readiness/overlap/transition enforcement; no new Frappe shell, header, breadcrumb, or PE/FY selector inside the Vue page canvas.
