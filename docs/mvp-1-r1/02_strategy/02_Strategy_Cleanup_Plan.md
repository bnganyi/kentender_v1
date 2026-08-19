# Strategy Alignment cleanup — plan

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.0.md`, `01_Strategy_Cleanup_Audit_Report.md`
**Status:** Planned
**Tracker:** `03_Strategy_Cleanup_Tracker.md`

## Locked decisions

| Decision | Locked outcome |
|---|---|
| Rebuild posture | Correction-in-place, not delete-and-recreate. `kentender_strategy` is substantively retained per STR-CHG-001 §1. |
| Compatibility layer | None. No alias, redirect, dual read, shadow write, or feature flag for any renamed/removed concept (STR-CHG-001 §1.3). |
| Strategy Corrective Action | Remove entirely — doctype, services, page, nav entry. |
| Strategy performance page | Strip treatment logic; keep the page as a neutral, permission-gated read surface. |
| XMOD-STR-005 (Tender/Award carry) | Provider-side lineage/snapshot contract proceeds in this cleanup. Downstream Tender/Award consumer work is deferred to a separate, future change unit. |
| XMOD-STR-008 (remediation notifications) | Cancelled as superseded (its trigger, corrective actions, is being removed). Not deferred, not rebuilt. |
| Downstream ripple boundary | `kentender_budget`'s existing Strategy imports/queries are updated in this same effort (mechanical, forced by the no-alias rule) — including closing the raw-DB-query fallback in `kentender_mvp_v1_portfolio.py`. `kentender_procurement`'s seed-orchestration imports of Strategy seed helpers are updated only for renamed identifiers they reference, not redesigned. Procurement Planning is not touched (no current Strategy import exists there). |
| Objective/Outcome/Indicator | Introduce an explicit Strategic Objective concept distinct from Strategic Outcome (currently missing); fix `REF_TYPE_META` to stop mapping `"OBJ"` to Public Value Objective. |
| Pre-existing dangling `kentender_procurement.demands` imports outside `kentender_strategy` | Out of this cleanup's boundary (Procurement Home, Procurement Planning, Core seeds) — pre-existing, already-accepted breakage per the Departmental Needs tracker's RBD-G02. Not touched here. |

## Phases

### Phase 0 — Unblock (prerequisite to everything else)

Fix the dangling `kentender_procurement.procurement_lifecycle.demand_module_gate` import so the test suite can collect at all. Without this, no phase below can be verified.

- Remove/replace the import in `services/strategy_performance.py`, `seeds/moh_downstream_usage.py`, `tests/test_dem_int_008_strategy_pvc_adoption.py`.
- `test_dem_int_008_strategy_pvc_adoption.py` is a Demand-integration leftover tied to the now-cancelled XMOD-STR-008 — delete it rather than repair it (confirm no other assertions in it are still load-bearing first).
- Confirm `bench --site kentender.midas.com run-tests --app kentender_strategy` reaches collection and produces a real pass/fail baseline.

### Phase 1 — Rename Plan Value Commitment → Strategy Value Commitment

- DocTypes: `plan_value_commitment/` → `strategy_value_commitment/`, `plan_value_commitment_link/` → `strategy_value_commitment_link/` (child table). No alias doctype.
- All references across `strategy_writes.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_contracts.py`, `strategy_performance.py`, `strategy_domain_guards.py`, `strategy_api.py`.
- UI labels, routes, JS fixtures, hooks page_js entries.
- Seeds and tests referencing the old name.
- Downstream ripple: `kentender_budget/services/budget_contracts.py`, `budget_revision_contracts.py` (label text), `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` (raw-query fallback — see Phase 7), `kentender_core/seeds/kentender_mvp_v1/validate.py`, `kentender_core/patches/v1_0/drop_legacy_owner_state_directorate_fields.py` (expected — schema patch), Procurement Plan Item Version's "Plan Value Commitment Snapshot" field label.

### Phase 2 — Remove Public Value Objective (PVO) engine

- Delete doctype `public_value_objective/`.
- Remove all PVO logic from `strategy_contracts.py`, `strategy_domain_guards.py`, `strategy_notification_service.py`, `strategy_reference.py`, `strategy_readiness.py`, `strategy_writes.py`, `strategy_transitions.py`, `strategy_api.py`.
- Delete pages: `strategy_pvo_catalogue_page.js` + `page/strategy_pvo_catalogue/`, `strategy_pvo_editor_page.js` + `page/strategy_pvo_editor/`.
- Delete JS fixtures: `strategy_ui_fixtures/pvo_catalogue.js`, `pvo_editor.js`.
- Remove the two `hooks.py` `page_js` routes (`strategy-pvo-catalogue`, `strategy-pvo-editor`) and their CSS/JS includes.
- Remove PVO nav labels from `kentender_core/public/js/kt_cl_surface_registry.js`.
- Remove PVO-referencing seeds and tests (or rewrite where the test also covers still-valid behavior).

### Phase 3 — Remove treatment logic and Strategy Corrective Action

- Remove "treatment" business logic from `strategy_performance.py`.
- Delete doctype `strategy_corrective_action/`, its page `strategy_corrective_actions_page.js`, and all service references.
- Remove the corrective-action nav entry and hooks routes.
- Strip (don't delete) the performance page down to a neutral read surface per the locked decision above.

### Phase 4 — Objective/Outcome/Indicator semantic correction

- Design and introduce an explicit Strategic Objective concept (new doctype, or a typed node consistent with how `Strategic Outcome`/`Performance Indicator` already exist as standalone doctypes — match their pattern, don't reintroduce the old conflated `strategy_objective`).
- Fix `REF_TYPE_META` in `strategy_reference.py`: add a `"Strategic Objective"` entry, remove the `"OBJ" → "Public Value Objective"` mapping (superseded by Phase 2's removal in any case).
- Validate STR-CHG-001 §6.2 invariants: "A Performance Indicator measures one Strategic Objective or Strategic Outcome; it is not itself an objective."

### Phase 5 — Replace Administrator/fallback authority patterns

- `strategy_reference.py::can_correct_reference()` — replace the `System Manager`/`Administrator` gate with an explicit Strategy capability check (Author/Reviewer/Approval Authority per STR-CHG-001 §8).
- `strategy_permissions.py` (lines 41, 48, 90) and `strategy_performance.py` (lines 66, 73, 802) — same replacement.
- `strategy_reference.py::resolve_pe_for_doc()` — make PE resolution fail-closed (raise a controlled, typed error) instead of silently returning `None`.
- Seed files (`kentender_mvp_v1_strategy.py`, `works_master_strategy_hierarchy.py`, others) — replace hardcoded `"Administrator"` actors with real seeded Strategy Author/Reviewer/Approval Authority persona users, matching the Departmental Needs precedent (seeded reviewer/delegate personas, `Test@123` passwords).

### Phase 6 — Harden active-plan-overlap uniqueness

- Review `strategy_domain_guards.py::normalize_plan_scope()`'s existing "legacy rows" fallback comment; harden or remove depending on whether it's still reachable after Phases 1–5.
- Add/confirm a concurrent-activation test (STR-CHG-001 §18 risk: "Multiple active plans create ambiguous lineage").

### Phase 7 — Implement the STR-CHG-001 §12 integration contracts; close the Budget raw-query fallback

- Implement or formally adapt existing functions to the five named contracts: `resolve_strategy_context`, `list_strategy_commitments`, `get_strategy_lineage`, `create_strategy_snapshot` (in scope); `record_verified_result` (stub only — explicitly deferred to Contract Management scope per STR-CHG-001 §12).
- Migrate `kentender_budget`'s existing consumer calls (`strategy_consumer.apply_budget_primary_strategy_reference`, `resolve_performance_target_id`, `validated_supporting_target_row`, `strategy_reference.pe_slug`, `strategy_api.list_active_targets`) onto the new contract names where they overlap, or confirm they already satisfy the contract shape and only need the Phase 1 rename ripple.
- Close the raw-DB-query `except ImportError` fallback in `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` (~lines 489–536) — it must call the contract or fail loudly, not silently read Strategy tables directly.
- Update `kentender_budget/tests/test_budget_line_strategy_validate.py`'s direct `frappe.db.get_value` call and seed-helper import for the Phase 1 rename.

### Phase 8 — Seed rebuild

- Rebuild deterministic MoH/Kisumu seeds per STR-CHG-001 §13: `STR-MOH-2023-001`, MoH hierarchy (digital health pillar → programme → sub-programme → objective → outcome → indicator → FY 2027/28 target), `SVC-MOH-2027-001` Strategy Value Commitment, `STR-KSM-2023-001`.
- Seed must fail loudly on missing CFG (PE/FY) prerequisites — no first-PE/first-record fallback creation.
- Confirm idempotent double-run (STR-AC-014).
- Update `kentender_procurement/procurement_lifecycle` seed-orchestration call sites (`works_master_full_seed.py`, `purge_non_works_master_seed.py`) for renamed Strategy identifiers only — no redesign of those files.

### Phase 9 — Test suite and verification

- Fix/rewrite the flagged test files (audit §7); delete `test_dem_int_008_strategy_pvc_adoption.py` per Phase 0.
- Add coverage for STR-FR-001 through STR-FR-022 and STR-AC-001 through STR-AC-018 where not already covered.
- Run the STR-CHG-001 §16 smoke contract in full: static dependency scan, fresh-environment install/migrate/seed, module import isolation, seed repeatability, domain tests, permission tests, integration tests (Budget context resolution + snapshot), browser smoke.
- Update this plan's tracker with final evidence; do not revive the retired `docs/mvp-1/01_strategy` documents (STR-CHG-001 §14 step 10).

## Explicitly out of scope

- Any redesign of Procurement Planning, Tender, or Contract Management beyond consuming the stable read contracts this plan defines (STR-CHG-001 §1.3).
- Tender/Award's consumption of the strategy-lineage/snapshot contract (XMOD-STR-005 downstream half) — deferred to a separate change unit.
- Remediation-notification workflow (XMOD-STR-008) — cancelled, not rebuilt.
- Any dangling `kentender_procurement.demands` import outside `kentender_strategy` (Procurement Home, Procurement Planning, Core seeds) — pre-existing, accepted breakage tracked under the Departmental Needs tracker's RBD-G02, not this plan's responsibility.
- A generic Public Value Objective rules engine or advanced performance-management suite — explicitly excluded by STR-CHG-001 §1.3, not deferred, not built toward.

## Sequencing rationale

Phase 0 must complete first — every other phase needs a working test collection to verify against. Phases 1–3 (rename/remove) are largely mechanical and low-risk once Phase 0 is done, and should happen before Phase 4 (semantic correction) since Phase 4's `REF_TYPE_META` fix is partly a consequence of Phase 2's PVO removal. Phase 5 (fallback/authority) and Phase 6 (overlap hardening) are independent of 1–4 and can run in parallel with them if useful, but are sequenced after for tracker clarity. Phase 7 (integration contracts) depends on Phases 1 and 2 being complete (the contracts must return Strategy Value Commitment references, not Plan Value Commitment or PVO ones). Phase 8 (seeds) depends on Phase 7's contracts existing, since seed correctness is partly verified through them. Phase 9 (verification) is last by definition.
