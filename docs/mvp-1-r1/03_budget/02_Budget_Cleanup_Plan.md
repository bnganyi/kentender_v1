# Budget & Funding cleanup — plan

**Authority:** `KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1.0.md`, `01_Budget_Cleanup_Audit_Report.md`
**Status:** Planned — approved. BUD-CHG-001 §19 shows Approved (product-owner approval, bnganyi, 2026-08-20); implementation may proceed.
**Tracker:** `03_Budget_Cleanup_Tracker.md`

## Locked decisions

| Decision | Locked outcome |
|---|---|
| Rebuild posture | Correction-and-completion in place, not delete-and-recreate. `kentender_budget` is substantively retained; several load-bearing pieces (baseline-registration model, core arithmetic, absence of PVO/Allocation terminology) are already correct per audit §2 and must be confirmed, not rebuilt. |
| Compatibility layer | None. No alias, redirect, dual read, shadow write, or feature flag for any renamed/removed concept, matching BUD-CHG-001 §1.3/§5 and the Strategy precedent. |
| Budget Line Value Treatment | Remove entirely — doctype, child-table field, rollup fields, all service logic (including the duplicated `_value_treatment_summary` in two files), readiness-checklist coupling, seed data, UI/CSS. No "read-only display" carve-out — BUD-CHG-001 §5 says "No replacement." |
| Fixture reference codes | **Audit-and-confirm substance, don't force a rename onto a working generator** (audit §7 precedent, same judgment call as Strategy Phase 4/8). Verify the seed's dollar amounts and PE/FY scoping hit BUD-CHG-001 §13.1's canonical arithmetic; do not redesign `budget_reference.py`'s live auto-numbering scheme to match the spec's illustrative fiscal-year-coded example codes unless the product owner confirms those codes are meant literally. |
| `dia_budget_control.py` | Retained as the downstream-facing API adapter (a legitimate post-teardown rebuild, not the leftover the prior teardown doc expected gone) — but its functions must be made to delegate to the same named services-layer contracts `budget_api.py` exposes, not carry independent inline logic, closing audit §4's duplication risk. |
| §12 integration contracts | Implement the 6 genuinely missing contracts (`resolve_budget_context`, `revalidate_reservation`, `release_reservation` [service layer], `convert_reservation`, `adjust_commitment`, `ingest_expenditure_snapshot`) as new construction; formally rename/consolidate the 2 existing-under-a-different-name contracts (`list_active_lines_for_check` → `list_eligible_budget_lines`, `list_downstream_usage`/`get_budget_usage` → `get_funding_lineage`, resolving that file's own internal alias first); confirm the 3 verbatim-name contracts (`check_funding`, `reserve_funding`, `apply_budget_revision`) against BUD-CHG-001's actual requirement text before assuming their existing behavior is compliant. |
| UI screen numbering | **Revised during Phase 1 implementation — do not remap routes.** The `BUD-UI-XX` numbers in `kentender_budget`'s code are a deliberate, internally-consistent, actively-tested numbering scheme of their own (a pre-BUD-CHG-001 "Contract v2.0"/"Pack" convention — UI-02=Performance, UI-04/05=Lines+Editor, UI-06=Check/Reserve, UI-10=Downstream, UI-11=Review, UI-12=Audit), not drift: `test_budget_ui_stitch_layout_guard.py` directly asserts the registry maps `"BUD-UI-02"` to the Funding Performance route specifically, not Register. Forcing these onto BUD-CHG-001's different 10-item numbering would mean rewriting ~25+ files (route slugs, the `Page` doctype folder for each, `hooks.py` `page_js` keys, `kentender_core`'s `stitch_desk_chrome_registry.py`/`module_registry.py`/`kt_module_registry.js`/`kt_cl_surface_registry.js`, `my_work.py`'s task-routing tuples) plus 7+ Playwright specs and 2 asserting Python tests that check exact on-screen heading text (`"Check and reserve funding"`, `"Readiness Checklist"`) — for a purely cosmetic renumbering with no BUD-CHG-001 functional requirement behind it (the spec names screens by capability, not URL slug or internal doc-comment number). Same judgment call as the fixture-reference-code decision above: **keep the working, tested, internally-coherent numbering; do not force a rename onto it.** Only genuinely uncontested, zero-blast-radius items proceed (see Phase 1 below). |
| Role model | **Revised during Phase 4 implementation — no new Frappe Role records.** Reading the actual gating code showed the conflation was one shared *capability string* (`budget.approve`, used by both Activation and Revision-apply/reject), not a shared Role — `activate_budget` already ran through the real PE/OU/FY-scoped capability/task system (`kentender_core.services.authorization_policy`), which independently satisfies BUD-CHG-001 §8.1's assignment-model requirement. Introduced 2 new capability strings (`budget.revision.apply`, `budget.reserve`) instead of new Roles, resolved through that same existing system — avoiding exactly the "parallel mechanism" the original plan wording warned against. |
| `reserve_funding`'s Demand coupling | Audit its body directly before deciding: if it genuinely reserves against Demand acceptance rather than a completed Plan Item, correct it to gate on Plan Item completeness per BUD-FR-009/012; if the `demand_name` parameter turns out to be correlation/audit labeling only, confirm and close with evidence rather than rewrite a compliant function. |

## Phases

### Phase 0 — Establish baseline

Unlike Strategy, no known collection-blocking import was found. Still required before any other phase, since none of it can be verified against an unknown baseline.

- Run `bench --site kentender.midas.com run-tests --app kentender_budget`; record pass/fail/error counts by test file.
- If collection fails, diagnose and fix before proceeding (mirrors Strategy Phase 0's role, contingent on what's actually found — not assumed broken).
- Confirm whether `kentender_budget`'s test suite currently depends on `kentender_strategy` fixtures being seeded first (Budget Line's Strategy-resolution logic suggests it might) and document the required seed order.

### Phase 1 — UI screen numbering confirmation and terminology corrections

**Re-scoped during implementation** (see the "UI screen numbering" locked decision above). A full-repo grep for every route string involved (`budget-review`, `budget-audit`, `budget-check-reserve`, `budget-downstream`) showed the blast radius is far larger than the audit could see from `kentender_budget` alone — it reaches into `kentender_core`'s cross-app registries and task-routing table, plus 7+ Playwright specs, plus 2 Python tests that assert exact on-screen heading text. The `BUD-UI-XX` numbers turned out to be a deliberate, self-consistent, already-tested internal convention, not stale drift. Original scope (route rename, workspace-tab restructuring, hooks.py changes) is **not executed**. What actually proceeds:

- Confirm (not rename) the existing `BUD-UI-XX` numbering is internally coherent and leave it untouched — audit §6's "stale citation" framing is corrected here to "different, pre-existing, coherent internal convention."
- Cosmetic-only: rename the `<h2>Budget Allocation</h2>` heading in `budget_ui_fixtures/check_reserve.js` (no backing doctype, no test/spec assertion on that exact string — confirmed by a targeted grep before editing, distinct from an unrelated legacy-doctype-absence test that coincidentally shares the string "Budget Allocation").
- No route rename, no `hooks.py` change, no `budget_workspace_shell.js` tab-list change, no `kentender_core` registry change, no Playwright spec change — all explicitly deferred, not silently dropped, pending an explicit product-owner call on whether the cosmetic renumbering is worth a dedicated, isolated future pass.

### Phase 2 — Remove Budget Line Value Treatment entirely

- Delete doctype `budget_line_value_treatment/`.
- Remove `Budget Line.value_treatments` Table field and `Budget.strategy_pvc_treated`/`strategy_pvc_applicable` rollup fields.
- Remove from `budget_line_contracts.py`: `_treatment_dtos`, `_dedicated_total`, `_refresh_budget_pvc_counts`, `_TREATMENTS_NEEDING_RATIONALE`, and the save-payload validation block requiring dedicated amounts/rationale/`reviewer_accepted`.
- Remove the duplicated `_value_treatment_summary()` helper from both `budget_check_reserve_contracts.py` and `budget_funding_performance_contracts.py` (and whatever summary fields it feeds in each file's DTO).
- Remove the readiness-checklist evaluation of `value_treatments` completeness from `budget_readiness_contracts.py`.
- Remove the `"Value treatment changed"` option from `Budget Audit Event.event_type`.
- Remove seed constants `_PVC_TREATMENTS_DHI/HWD/CGK` and their loop-building code from `kentender_mvp_v1_portfolio.py`; confirm `set_budget_line_allocation_by_code`'s existing no-op guard (it already defensively checks `meta.has_field("amount_allocated")`, a field that has never existed) doesn't need updating, since it isn't treatment-related.
- Remove CSS class `.kt-bud-perf-treatment`; remove treatment `<select>` rendering/binding from `budget_live_bind.js` and treatment headings/columns from `budget_ui_fixtures/{lines,performance,revision_review}.js`.
- **Verify BUD-CHG-001 §2 problem-table row 4 (double-subtracted actual expenditure) stays resolved** after removing the two value-treatment summary read paths — confirm neither one was independently re-deriving an available/outstanding figure that diverged from `Budget Line.validate()`'s already-correct formula (audit §2 flagged this as unconfirmed, not clean).

### Phase 3 — Confirm zero-or-more Strategy reference cardinality

- Read `Budget Line.validate()`'s Strategy-resolution block directly to confirm `primary_target_id` is not enforced as mandatory (audit §3 flagged this as unconfirmed).
- If already optional: close with a confirmation note and a test proving a Budget Line saves cleanly with zero Strategy references, matching BUD-CHG-001 §5's "zero-or-more approved refs, no questionnaire" requirement.
- If found mandatory: relax the validation, matching the same requirement.

### Phase 4 — Role model correction

**Re-scoped during implementation** (see the "Role model" locked decision above). Reading `budget_check_reserve_contracts.py`'s and `budget_readiness_contracts.py`'s actual gating code directly showed: `check_funding`/`reserve_funding` had zero capability-system integration at all (pure role-list check); `activate_budget` already ran entirely through `kentender_core.services.authorization_policy`'s capability/task system (its `_ACTIVATE_ROLES` role constant was dead code); and the real Activation/Revision conflation was `apply_budget_revision`/`reject_budget_revision` sharing `activate_budget`'s exact capability string (`budget.approve`), not a shared Role. What actually proceeded:

- Added `CAP_BUDGET_REVISION_APPLY` and `CAP_BUDGET_RESERVE` capability constants to `budget_authorization.py`, resolved through the existing PE/OU/FY-scoped `evaluate_capability`/`require_capability` system — confirmed to already satisfy §8.1's assignment-model requirement, so no parallel mechanism was built.
- `budget_revision_contracts.py`: moved `apply_budget_revision`/`reject_budget_revision` off `CAP_BUDGET_APPROVE` onto `CAP_BUDGET_REVISION_APPLY`, at every site in the submit→review→apply/reject chain (task creation, task consumption, the review-context commands check, the revision-list open-action check); removed the redundant role-layer pre-filter + inline Administrator bypass both functions carried, matching `activate_budget`'s already-correct capability-only shape.
- `budget_check_reserve_contracts.py`: wired `reserve_funding` into the capability system for the first time, via `require_budget_capability(CAP_BUDGET_RESERVE, bud)`; `check_funding` (read-only) kept on its existing broad role gate.
- Seed personas: 2 new distinct test users (`moh.budget.revision.authority@example.test`, `moh.budget.finance.officer@example.test`), each with a dedicated single-capability Capability Profile, proving genuine independent assignability — live-verified via `evaluate_capability`.
- Removed 4 confirmed-dead role constants found during this investigation (`_ACTIVATE_ROLES`, `_APPLY_ROLES`, `_SUBMIT_ROLES`, `_REVIEW_ROLES` in `budget_readiness_contracts.py`/`budget_revision_contracts.py`).

### Phase 5 — Remove Administrator/PE-MOH fallback patterns

- `budget_permissions.py::user_roles()` and `::require_any_role()` — remove the `Administrator`-identity bypass, keep the `System Manager`-role bypass (same distinction Strategy Phase 5 drew).
- `budget_permissions.py::entity_for_user()` — remove both `PE-MOH` hardcoded fallbacks (Administrator/Guest case, and the "no permitted entities" case); fail closed (raise a controlled, typed error) instead, matching Strategy's `resolve_pe_for_doc()` fix.
- `budget_contracts.py::resolve_scoped_entity()` — remove the Administrator-session bypass; keep the explicit-test-role-injection path already noted as intentional in its own comment.
- `budget_check_reserve_contracts.py` (~line 387) and `budget_funding_performance_contracts.py` (~lines 159, 162–163) — remove the Administrator PE-scope exemption and the documented `PE-MOH` "prefer seed entity" fallback.
- `budget_revision_contracts.py::reject_budget_revision()`/`::apply_budget_revision()` — remove the Administrator bypass from both; rely on the Phase 4 Revision Authority capability check alone.
- Sweep the rest of the app for un-named `.first(`/`limit=1`-style fallback patterns not caught by the audit's targeted grep (mirrors Strategy's SCL-506) — audit found none, but this must be confirmed with a broader pass, not assumed from one grep.

### Phase 6 — No-reservation-at-Demand-acceptance correction; resolve the `dia_budget_control.py` duplication

- Read `reserve_funding()`'s full body. Determine whether `demand_name` gates the reservation directly (a BUD-FR-009/012 violation) or is correlation/audit metadata only.
- If a violation is confirmed: correct the trigger to require a completed Plan Item reference instead, matching BUD-CHG-001 §9/§12.1's "Plan Item complete → Finance check-reserve" control point. Update `reserve_funding`'s stale `"BUD-FR-062–066"` docstring citation to the correct BUD-FR-00X numbers regardless of which way this resolves.
- Read `dia_budget_control.create_reservation`/`release_reservation`/etc. bodies directly against their `budget_check_reserve_contracts`/services-layer counterparts. If they duplicate logic rather than delegate, refactor `dia_budget_control.py` to call the services-layer contracts (existing ones now, the Phase 7 new ones once built) instead of carrying independent logic — closing audit §4's structural risk.
- Add a service-layer `release_reservation` function (currently API-layer-only per audit §5) that `dia_budget_control.py`'s adapter calls, rather than leaving it as the sole implementation.

### Phase 7 — Implement the BUD-CHG-001 §12 integration contracts

- New construction: `resolve_budget_context`, `revalidate_reservation`, `convert_reservation`, `adjust_commitment`, `ingest_expenditure_snapshot` — design each against its BUD-FR-0XX citation in §9 and its control-point row in §12.1, using the existing `Funding Reservation`/`Procurement Commitment`/`Expenditure Snapshot` doctypes' already-present status/amount fields (audit §5 confirmed the data model anticipates these transitions even though no service function drives them yet).
- Rename/consolidate: `list_active_lines_for_check` → `list_eligible_budget_lines` (or confirm the existing name already satisfies the contract and only needs a formal designation, product-owner's call); resolve `list_downstream_usage`/`get_budget_usage`'s internal alias down to one name, then align it to `get_funding_lineage`.
- Confirm `check_funding`, `reserve_funding` (post-Phase-6 correction), and `apply_budget_revision` against their actual BUD-FR-0XX text — not just their existing docstrings, several of which cite stale requirement numbers (audit §6).
- Update `budget_api.py` to re-export every §12 contract under its formal name, and confirm `dia_budget_control.py` (post-Phase-6 refactor) consumes the same functions.
- Add/confirm idempotency-key handling on every mutating contract (`reserve_funding`, `convert_reservation`, `adjust_commitment`, `ingest_expenditure_snapshot`) per BUD-CHG-001 §11's row for idempotent correlation keys.

### Phase 8 — Seed audit and reconciliation

- Confirm the live seed's reservation/commitment amounts against BUD-CHG-001 §13.1's full canonical arithmetic fixture (480M approved → 455M reservation → 310M commitment → 145M remaining reservation → 25M available) — audit §7 confirmed the two approved-amount anchors (480M, 80M) already match; the reservation/commitment figures need direct confirmation.
- Confirm the no-expenditure-fixture rule (§13: no Expenditure Snapshot rows in the base seed) and that negative/edge fixtures stay test-only, not in the base portfolio seed.
- Confirm MoH/Kisumu PE isolation and idempotent double-run (rerun `upsert_kentender_mvp_v1_portfolio()` twice, confirm no duplicate rows) — add a dedicated test if one doesn't already exist, matching Strategy's `test_seed_double_run_is_idempotent`/`test_seed_double_run_creates_no_duplicate_rows` pattern.
- Do **not** rename the seed's auto-generated reference codes (`MOH-BUD-0002`, `MOH-BL-0003`/`0004`) to match BUD-CHG-001 §13's illustrative fiscal-year-coded examples, per the locked decision above — confirm this reading with the product owner if it's in doubt before closing this phase.
- Confirm the `moh_mvp_v1_portfolio.py` deprecated shim has no remaining live callers before considering its removal (out of BUD-CHG-001's explicit scope unless a caller sweep finds it still load-bearing).

### Phase 9 — Test suite and verification

- Fix/rewrite the stale-citation test files identified in audit §10 and Phase 1 (`test_budget_readiness.py`, `test_budget_audit.py`, `test_budget_downstream_usage.py`, `test_budget_check_reserve.py` label only).
- Add coverage for BUD-FR-001 through BUD-FR-030 and BUD-AC-001 through BUD-AC-024 where not already covered — cross-check each file's own coverage-map claims against actual assertions, matching the Strategy Phase 9 precedent of correcting false "yes, covered" claims found along the way.
- Run the BUD-CHG-001 §16 smoke contract in full: static dependency scan (no `kentender_procurement.demands`/`demand_module_gate`/treatment-concept imports), fresh-environment install/migrate/seed (CFG → optional Strategy seed → Budget seed), seed repeatability, arithmetic (§13.1's full fixture story), atomicity, lifecycle, permissions, integration, browser smoke.
- Update the tracker with final evidence; do not revive `docs/mvp-1/02_budget/*` as a live authority (matches BUD-CHG-001's own supersession framing).

## Explicitly out of scope

- Any redesign of Departmental Needs, Procurement Planning, Tender, or Contract Management beyond consuming the §12 contracts this plan builds/confirms.
- Advanced Funding Performance analytics beyond the Operational Funding Position strip already scoped (BUD-CHG-001 §14.2: "advanced analytics deferred").
- Award/Contract's full conversion-workflow consumption of `convert_reservation` — BUD-CHG-001 §14.2 marks this "required-with-gate," meaning the contract itself is built here, but a live Award/Contract module wiring into it is that module's own future change unit, not this plan's.
- `record_verified_result`-equivalent deferred stubs, if any surface during Phase 7 design, follow the same explicit-stub, not-silently-omitted treatment Strategy used for its own deferred contract.
- Removing `dia_budget_control.py` or `moh_mvp_v1_portfolio.py` outright — both are retained (refactored in place for the former, confirmed-unused-or-left for the latter) per the locked decisions above, not deleted.

## Sequencing rationale

Phase 0 establishes a baseline every later phase needs to verify against. Phases 1–3 (renumbering, treatment removal, Strategy-cardinality confirmation) are mechanical-to-moderate and independent of the higher-uncertainty findings, so they clear first. Phase 4 (role model) and Phase 5 (Administrator/PE-MOH fallback) are sequenced before Phase 6 because Phase 6's `dia_budget_control.py` refactor should call correctly-capability-gated functions, not functions still carrying the old shared-role/Administrator-bypass pattern. Phase 6 (Demand-coupling correction, `dia_budget_control.py` consolidation) must resolve before Phase 7, since Phase 7 explicitly builds `release_reservation` and the other contracts on top of whichever pattern Phase 6 confirms or corrects — building new contracts before knowing whether the existing reservation flow is compliant would risk replicating the same defect into new code. Phase 8 (seed audit) depends on Phase 7's contracts existing, since the arithmetic-fixture confirmation is partly verified by calling them directly, matching Strategy's own Phase 7→8 dependency. Phase 9 (verification) is last by definition.
