# Strategy Alignment cleanup — audit report

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.0.md` (sole current authority for this module; supersedes all `docs/mvp-1/01_strategy/*` documents — see §1 below)
**Date:** 19 August 2026
**Scope of this document:** bridge STR-CHG-001's requirements against the actual state of `kentender_strategy` and its consumers, so the cleanup plan and tracker are grounded in real file paths, not assumptions.

## 1. Governing-document chain

STR-CHG-001 (`docs/mvp-1-r1/02_strategy/KenTender_STR-CHG-001_...md`) states plainly: *"The module is substantively retained. The work is a controlled semantic and dependency correction, not a complete functional rewrite."* This is a materially different posture from the Departmental Needs rebuild (delete-and-rebuild greenfield) — Strategy is **patched and corrected in place**, not deleted and replaced.

Cross-checked the four original `docs/mvp-1/01_strategy/*` documents most likely to contain a prior teardown inventory:

| Document | Finding |
|---|---|
| `05_Strategy_Teardown_Dependency_Inventory.md` | Documents a **prior, already-completed** teardown (dated 2–6 Aug 2026). Its "current concepts" (Strategic Outcome, Performance Indicator, PVO, Plan Value Commitment, Strategy Corrective Action) are exactly what STR-CHG-001 now targets for further rename/removal. This doc treats them as the finished, correct product — it does not anticipate STR-CHG-001. |
| `08_Strategy_Cross_Module_Lifecycle_Tracker.md` | Tracks Strategy→downstream integration points (Budget, Demand, Planning). Status snapshot: "Strategy Core Complete + Integration Ready." Two rows are genuinely incomplete: XMOD-STR-005 (Tender/Award carry) and XMOD-STR-008 (remediation notifications), both "Provider complete — consumer pending." No row flags Demands-coupling, PVO, or Administrator fallback as defects. |
| `04_Strategy_Alignment_MVP1_Requirements.md` | Defines the *current* terminology (including "Plan Value Commitment") as intended design, not legacy. |
| `06_Strategy_Alignment_MVP1_Cursor_Implementation_Prompt.md` | Predates STR-CHG-001; generic "no compatibility adapter" guardrails only, nothing specific to this correction. |

**Conclusion:** none of the original docs identify STR-CHG-001's targets as problems. STR-CHG-001 is a genuinely new, second correction pass over an already-"shipped" module. The original docs are retained for historical record only and are not used to scope this cleanup.

## 2. Current state: the module is actively broken

`bench --site kentender.midas.com run-tests --app kentender_strategy` fails at **test discovery**, before any test executes:

```
ModuleNotFoundError: No module named 'kentender_procurement.procurement_lifecycle.demand_module_gate'
```

raised while importing `test_strategy_performance.py` → `kentender_strategy/services/strategy_performance.py:15`. That module was deleted along with the rest of the legacy Demands package in an earlier, unrelated effort (the Departmental Needs greenfield rebuild's Phase 1). Two more files carry the same dangling import:

- `kentender_strategy/kentender_strategy/services/strategy_performance.py:15`
- `kentender_strategy/kentender_strategy/seeds/moh_downstream_usage.py:10`
- `kentender_strategy/kentender_strategy/tests/test_dem_int_008_strategy_pvc_adoption.py:11`

This directly matches STR-FR-020 ("Operate without ... any legacy demands package being importable") and is the single highest-priority fix: **no test evidence of any kind can be collected for this module until it is resolved.** It must be Phase 0, ahead of every other correction.

## 3. Rename/removal inventory (STR-CHG-001 §5 rename register, §14.1 removal checklist)

| STR-CHG-001 target | Current state (concrete paths) | Disposition |
|---|---|---|
| "Plan Value Commitment" → "Strategy Value Commitment" | DocTypes `plan_value_commitment/`, `plan_value_commitment_link/` (child table). Referenced in `strategy_writes.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_contracts.py`, `strategy_performance.py`, `strategy_domain_guards.py`, `strategy_api.py`; also in `kentender_budget` (contract labels, one seed fallback), `kentender_core/seeds/kentender_mvp_v1/validate.py`, a Core patch, and one Procurement Plan Item Version field label ("... Snapshot"). 154 repo-wide hits total. | Full rename, no alias, per §1.3/§5. Ripple into `kentender_budget`/`kentender_core` is unavoidable and in scope (compat shims are explicitly forbidden). |
| "Public Value Objective" (PVO) engine | DocType `public_value_objective/`; services `strategy_contracts.py`, `strategy_domain_guards.py`, `strategy_notification_service.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_writes.py`, `strategy_transitions.py`, `strategy_api.py`; pages `strategy_pvo_catalogue_page.js` + `page/strategy_pvo_catalogue/`, `strategy_pvo_editor_page.js` + `page/strategy_pvo_editor/`; JS fixtures `strategy_ui_fixtures/pvo_catalogue.js`, `pvo_editor.js`; two `hooks.py` `page_js` routes (`strategy-pvo-catalogue`, `strategy-pvo-editor`); nav labels in `kentender_core/public/js/kt_cl_surface_registry.js`. All ~80 remaining PVO hits are internal to `kentender_strategy`. | Full removal — doctype, services, pages, JS, hooks routes, nav labels, seeds, tests. Per §1.3: "No advanced ... Public Value Objective rules engine in MVP 1" and §14.1: "No Public Value Objective engine in MVP navigation, hooks or mandatory validations." |
| "Strategy treatment / planned treatment" | Business logic (not just naming) in `strategy_performance.py`. | Remove per §1.3/§5. |
| Objective/Outcome/Indicator conflation | `Performance Indicator` and `Strategic Outcome` **already exist as separate DocTypes** — the old conflated `strategy_objective` doctype was already dropped by a prior patch (`patches/mvp1_teardown_drop_legacy_strategy_doctypes.py`). But `REF_TYPE_META` in `strategy_reference.py` still maps `"OBJ" → "Public Value Objective"`, with **no "Strategic Objective" entry at all** — there is currently no doctype or reference type representing a genuine Strategic Objective distinct from an Outcome, contradicting STR-CHG-001 §6.1's hierarchy (`... → Strategic Objective → Strategic Outcome → Performance Indicator → Performance Target`). | Schema-level split is partially done; semantic wiring is not. Needs a scope decision in the plan: introduce a real `Strategic Objective` hierarchy-node concept (new doctype or a typed `Strategy Node`-equivalent), and fix `REF_TYPE_META`. |
| Strategy Corrective Action (out-of-MVP-1 per §1.3) | DocType `strategy_corrective_action/`, page `strategy_corrective_actions_page.js`, referenced in the audit/reference services. | **Decision (confirmed with product owner): remove entirely** — doctype, service references, page, nav entry. Treated as an out-of-scope feature under STR-CHG-001's exclusion, not grandfathered. |
| Advanced strategy-performance dashboard (out-of-MVP-1 per §1.3, §STR-UI-01) | `strategy_performance.py` (treatment logic + dashboard aggregation), `strategy_alignment_performance_page.js`. | **Decision (confirmed): strip, don't remove.** Delete the "treatment" business logic (a confirmed removal target regardless); keep the page itself as a neutral, permission-gated read surface — STR-CHG-001 only forbids the *workspace* from showing an advanced dashboard, not a dedicated screen elsewhere. |

## 4. Administrator-as-authority / silent-fallback inventory (§2, §7.1, §8, §11)

| Location | Pattern | STR-CHG-001 rule violated |
|---|---|---|
| `strategy_reference.py::can_correct_reference()` (~lines 114–116) | Gates reference corrections on `System Manager` or literal `Administrator`, documented as a "Strategy Administrator stand-in." | §8: Administrator has neutral read access only, unless explicitly assigned a Strategy role. |
| `strategy_permissions.py` (lines 41, 48, 90) | Uses `Administrator` as a permission bypass. | Same. |
| `strategy_performance.py` (lines 66, 73, 802) | Same pattern. | Same. |
| `strategy_reference.py::resolve_pe_for_doc()` (~line 148) | Explicitly commented `"Best-effort procuring entity for allocation"`; returns `None` silently when unresolved instead of raising. | §2 table ("Silent PE/OU selection... no first-record fallback") and §11 ("Explicit authorised PE/OU scope... never first-row fallback"). |
| `strategy_domain_guards.py::normalize_plan_scope()` (~lines 84–124) | Active-plan-overlap uniqueness check already exists, but carries an explicit "legacy rows" fallback comment. | Needs review/hardening, not a rebuild — lower risk than the items above. |
| Seed files: `kentender_mvp_v1_strategy.py`, `works_master_strategy_hierarchy.py` (heaviest), others | Hardcode `"Administrator"` as `benefit_owner` / `verified_by` / `submitted_by`. | Same anti-pattern at the fixture level; needs real Strategy Author/Reviewer/Approval Authority persona users, matching the precedent already set for Departmental Needs (seeded reviewer/delegate personas, `Test@123` passwords). |

No `first_pe`, `.first()`-style, or `planning_authority`-fallback patterns were found by name — either already absent, or present under different naming that will need a broader sweep during implementation (not assumed clean).

## 5. Cross-module coupling assessment

**Already clean (no action needed beyond the rename ripple):**
- `kentender_budget/services/budget_line_contracts.py`, `.../doctype/budget_line/budget_line.py` → `strategy_consumer.apply_budget_primary_strategy_reference`, `resolve_performance_target_id`, `validated_supporting_target_row`.
- `kentender_budget/services/budget_reference.py` → `strategy_reference.pe_slug`.
- `kentender_budget/public/js/budget_live_bind.js` → whitelisted API `kentender_strategy.api.strategy_api.list_active_targets`.

**Confirmed gap — the STR-CHG-001 §12 contracts don't exist yet under those names.** The spec mandates five logical contracts: `resolve_strategy_context`, `list_strategy_commitments`, `get_strategy_lineage`, `create_strategy_snapshot`, `record_verified_result` (the last explicitly deferred to Contract Management scope). None of these names appear in `services/` or `api/` today; the current consumer-facing surface (`strategy_consumer.py`, `strategy_api.py`) uses different function names that do roughly the same job in places. This is the largest implementation lift in the whole change unit — not a rename, a genuine new/adapted contract layer.

**Confirmed violation — raw-query fallback in a Budget seed (to be fixed in this effort, per product-owner decision):**
- `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` (~lines 489–536): imports `resolve_performance_target_id` from `strategy_consumer`, but its `except ImportError` branch falls back to raw `frappe.db.get_value("Performance Target"/"Plan Value Commitment"/"Public Value Objective", ...)` — a direct table read STR-CHG-001 §12 forbids ("Downstream modules must not import Strategy DocType controllers or query Strategy tables directly").

**Test-only coupling (lower priority, still needs the rename ripple):**
- `kentender_budget/tests/test_budget_line_strategy_validate.py` imports the seed helper `upsert_works_master_strategy_hierarchy` and does a direct `frappe.db.get_value("Performance Target", ...)`.

**Seed-orchestration coupling, not a contract violation but not a STR-CHG-001 contract either:**
- `kentender_procurement/procurement_lifecycle/{works_master_full_seed,purge_non_works_master_seed}.py` and three related tests import `kentender_strategy.seeds.{upsert_works_master_strategy_hierarchy, purge_non_works_strategy_hierarchy, verify_works_master_strategy_seed}` — these are seed utilities, unaffected by the rename except for internal field/doctype names they construct records against.

**Dangling `kentender_procurement.demands` imports found outside `kentender_strategy`** (context only — out of this module's boundary, not fixed here): `procurement_home/services/{home_pipeline,home_actions}.py`, `procurement_lifecycle/seeds/works_master_full_seed.py`, `procurement_planning/seeds/scn_pln_add_001.py`, `procurement_planning/tests/test_planning_mvp_seed_contract.py`, `kentender_core/seeds/kentender_mvp_v1/{demands,users}.py`. These are pre-existing, already-known breakage from the Departmental Needs Phase 1 deletion (documented in that module's own tracker, RBD-G02, as an accepted out-of-scope consequence) — not something this Strategy cleanup introduces or is responsible for.

**No Strategy entry in `kentender_procurement/workspace_sidebar/procurement.json`** — unlike Departmental Needs and Budget & Funding, Strategy Alignment's nav is not wired through the shared Workspace Sidebar JSON; it routes through `kt_cl_surface_registry.js`/`kt_module_registry.js`/`procurement_sidebar_header.js` client-side registries instead. Any removal of PVO catalogue/editor pages must update these registries, not the sidebar JSON.

**Planning has no current Strategy import at all.** STR-CHG-001 §4.2 expects Plan Items to "select or inherit approved Strategy Value Commitments," but Procurement Planning is itself in a known-broken, deferred state (per the Departmental Needs tracker's RBD-3xx boundary). This means the Planning-side half of the Strategy→Planning contract has no live consumer to test against right now — flagged as a sequencing risk, not a blocker, in the plan.

## 6. XMOD-STR-005 / XMOD-STR-008 disposition (confirmed with product owner)

- **XMOD-STR-005 (Tender/Award strategy carry):** provider-side lineage/read contract work proceeds as part of this cleanup (it's simply STR-CHG-001 §12's `get_strategy_lineage`/`create_strategy_snapshot` contracts). The **downstream consumer work in Tender/Award is explicitly deferred** — out of this cleanup's scope, to be picked up by Tender/Award's own change unit.
- **XMOD-STR-008 (remediation notifications):** **cancelled as superseded**, not deferred. Its originating trigger was the corrective-action workflow, which is being removed under this same cleanup (§3 above). There is no valid notification integration left to complete.

## 7. Test suite state

17 test files under `kentender_strategy/tests/`. All currently uncollectable (see §2). Once unblocked, flagged for direct rework:

- `test_strategy_plan_value_commitments.py` — full rename ripple.
- `test_dem_int_008_strategy_pvc_adoption.py` — imports the dead `demand_module_gate` directly; name itself is a Demand-integration leftover. Candidate for deletion/rewrite once XMOD-STR-008 is confirmed cancelled.
- `test_strategy_mvp1_domain.py`, `test_strategy_ui_stitch_layout_guard.py`, `test_strategy_mvp1_ac_matrix.py` — PVO references throughout.
- `test_strategy_plan_structure.py`, `test_strategy_plan_overview.py`, `test_strategy_plan_measurements.py` — PVC rename ripple.

Which of the remaining ~10 files pass in isolation is unknown until Phase 0 unblocks collection — this must be measured, not assumed, once the dangling import is fixed.

## 8. Summary of what this audit changes about scope

Unlike the Departmental Needs rebuild, this is **not** a delete-and-recreate effort. The plan that follows is organized as a sequence of *corrections* to a substantially-retained module, ordered so that:
1. The module becomes testable again (Phase 0) before anything else is attempted.
2. Renames and removals happen with real, enumerated file lists (this audit), not exploratory discovery mid-implementation.
3. Downstream ripple into `kentender_budget` is treated as in-scope and mechanical (import/query renames + the one raw-fallback fix), not as a separate deferred effort — because STR-CHG-001 forbids the compatibility shims that would otherwise let Strategy's rename ship without touching Budget.
4. Two features that already exist in code (Corrective Actions, Performance dashboard) receive an explicit, product-owner-confirmed disposition rather than being silently carried forward or silently deleted.
