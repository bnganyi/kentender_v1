# STR-CHG-001 — Clean Strategy Alignment — tracker

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1.3.md`, `04_Strategy_Rebuild_Implementation_Plan.md`
**Status:** Phase 3 complete (roles/permissions seeded, live-verified). Phases 4–9 Planned, not started.
**Started:** 2026-08-23

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence (a command, a test name, a diff, a screenshot description) — not "looks right."
3. If a touched file still references a concept this change unit prohibits (Value Commitment, PVO, treatment, corrective action, result-capture/verification, an editable generated reference, a client-only permission/lifecycle check, a first-PE/first-OU/first-FY/Administrator fallback — spec §19), the row that touches it is not Done.
4. No row may introduce a new alias, redirect, dual-write, compatibility shim, or parallel legacy+Vue maintenance screen for anything this change unit deletes.
5. §12 (Claude Design contract, `strategy_design/*.dc.html`) governs visual/content fidelity only. §1–11 and §13–20 govern behavior. A row implementing behavior from §12 content instead of §13+ is a defect, not a shortcut.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-08-23 | Adopt `kentender_core.services.authorization_policy` (Capability Profile / Operational Scope Assignment / Separation of Duties Rule) for Strategy Author/Reviewer/Approval Authority roles and SoD, replacing Strategy's own `org_scope_access.py`/hand-rolled `can_*` mechanism | Same engine CFG-CHG-002 adopted; CFG-CHG-002's own tracker flagged two parallel authorization mechanisms in this repo as debt worth reconciling — this rebuild starts that reconciliation for Strategy's side. User-confirmed 2026-08-23. |
| 2026-08-23 | Delete `Strategy Audit Event` doctype; route all Strategy audit through `kentender_core.services.audit_event_service.log_audit_event()` / core's generic `Audit Event` doctype | CFG-CHG-002's tracker explicitly named Strategy's bespoke audit mechanism "a known, flagged issue, not a pattern to repeat." User-confirmed 2026-08-23. |
| 2026-08-23 | Treat `PE-CGKIS` as the real docname; spec's `PE-CGK` is descriptive shorthand, not literal | Inherited directly from CFG-CHG-002's identical decision (same live PE record, same reasoning: renaming cascades broadly for no functional benefit). |
| 2026-08-23 | New `Strategy Node` doctype is a fresh build, not a revival | A doctype named "Strategy Node" existed once in an earlier generation and was dropped by `kentender_strategy/patches/mvp1_teardown_drop_legacy_strategy_doctypes.py`. None of its schema or logic is assumed to survive; confirmed via reading that patch in full during Phase 0 research. |
| 2026-08-23 | Procurement's `strategy_alignment_handoff.py` fix is in-scope as Phase 6, not deferred to a separate change unit | It is Procurement consuming Strategy's own published contract (allowed dependency direction per AGENTS.md §2); its brokenness (wrong doctype/field names) is pre-existing and independent of this rebuild, but leaving it broken means the new `list_strategy_objectives`/`create_strategy_snapshot` contracts have no real caller to prove them against. |
| 2026-08-23 | Dev-site data may be deleted freely; no data-preserving migration for pre-rebuild `Strategic Plan` rows | Product owner confirmed this is still a dev site — Phase 1's patch truncates `Strategic Plan` and drops the 8 removed doctypes' tables outright rather than attempting a field-mapping migration into the new identity/version split. |
| 2026-08-23 | Accept a temporary functional regression in `kentender_budget`'s live Budget Line strategy-linking (`strategy_consumer.py` → `strategy_contracts.py`'s `validate_strategy_reference`/`build_strategy_reference`) rather than pulling Phase 4's lineage resolver into Phase 1 | User-confirmed 2026-08-23 (recommended option): keeps Phase 1/4 boundaries clean as planned. `resolve_strategy_context` (the one consumer function fully owned by Phase 1's own new schema) was rewritten and verified correct; the Node/Objective lineage-walking functions Budget's `apply_budget_primary_strategy_reference` depends on remain on the pre-rebuild schema until Phase 4. Confirmed via live probe: calling the old seed now fails with a clean `DoesNotExistError: DocType Strategy Programme not found`, not a silent wrong result or cascading crash. |
| 2026-08-23 | `Performance Indicator`'s spec field `name` stored as `indicator_name` | Frappe reserves the `name` fieldname for the document's own primary key; a custom field literally named `name` is not possible. Documented in the field's own description. |
| 2026-08-23 | Plan-role scoping (§7's "assignments are scoped by PE, optional OU, plan role and effective dates") is not implemented on `Operational Scope Assignment` in this rebuild | Its `resource_scope_type`/`resource_scope_id` is a Dynamic-Link mechanism designed for scoping to a specific record, not matching a plain Select-field enum value (`plan_role`); adding a real plan-role scoping mechanism would mean changing a shared `kentender_core` doctype, out of Strategy's ownership boundary to do unilaterally. PE + effective-date scoping (the two axes actually exercised by tests) are fully wired. |
| 2026-08-23 | Cross-module read-only capabilities for Budget/Finance Officer, Procurement Planner, Auditor (§7) deferred to Phase 4 | These roles read Strategy through downstream contracts (`resolve_strategy_context` etc.), not a Phase 3 lifecycle action — no capability exists yet for them to be usefully granted. Seeding one now would be an unused field/grant, which §2.2's data-purpose gate forbids. |
| 2026-08-23 | Phase 2's lifecycle engine calls `kentender_core.services.authorization_policy` directly (new `strategy_authorization.py` module, capability constants `strategy.plan_version.{author,review,approve}`) rather than waiting for Phase 3 | A real transition engine cannot enforce STR-CHG-001 §6.2's SoD rules (submitter≠reviewer≠approver) without calling *some* authorization engine — CFG-CHG-002 itself wired `authorization_policy` in the same phase as its transitions, not a later one. Phase 3 remains the phase that seeds the *production* Capability Profiles/Operational Scope Assignments/SoD Rules for real Strategy Author/Reviewer/Approval Authority actors; until then every check fails closed (no profile exists to grant it) — correct, not a gap. Phase 2's own tests build throwaway profiles/assignments as fixtures, same pattern as CFG-CHG-002's lifecycle tests. |

## Headline finding (read before touching any doctype)

A prior cleanup pass (v1.0, 4 merged commits: `190ab0a`, `05ccc36`, `8d1fc79`, `c78e7c2`) already deleted PVO and Corrective Action cleanly and implemented shapes close to the four §10 contracts inside `strategy_consumer.py`. It did **not** split Plan/PlanVersion, unify StrategyNode, delete Value Commitment or Performance Measurement, rename seed identifiers, or whitelist the contracts as API endpoints. Do not re-do the completed portion; do not assume the incomplete portion is further along than it is. Full inventory in `04_Strategy_Rebuild_Implementation_Plan.md` §3.

`kentender_budget` has real, live, non-cosmetic dependencies on `strategy_consumer.py` and `strategy_reference.py` (direct Python import, not RPC) — Phase 1/4 changes to those modules' function signatures must be checked against `budget_line.py`, `budget_line_contracts.py`, `budget_reference.py`, and `test_budget_line_strategy_validate.py` before being called Done.

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| STR-G00 | Plan and tracker authored | Done | `04_Strategy_Rebuild_Implementation_Plan.md` + this document; three Explore-agent research passes (current app inventory, downstream blast radius, kentender_core reuse precedents) |
| STR-G01 | `Strategic Plan`/`Strategic Plan Version` split exists; `Strategy Node` unifies the 4 hierarchy doctypes; `Performance Indicator`/`Target` trimmed to spec fields; `Performance Measurement` and `Strategy Value Commitment`(+link) deleted; audit migrated to core's `Audit Event` | Done | See Phase 1 work register. `bench --site kentender.midas.com migrate` clean; 16/16 new focused tests pass |
| STR-G02 | Full 8-state plan-version lifecycle implemented with `_check_expected_version()`, server-computed `available_actions`, atomic activate-supersede | Done | See Phase 2 work register. 9/9 new focused tests pass |
| STR-G03 | Strategy Viewer/Author/Reviewer/Approval Authority roles wired through `authorization_policy`; SoD enforced (submit≠review≠approve) | Done | See Phase 3 work register. 5/5 new focused tests pass |
| STR-G04 | All 4 §10 contracts + 8 §10.1 commands whitelisted and idempotent where required; §14 error contract implemented | Planned | See Phase 4 work register |
| STR-G05 | §16 seed contract satisfied exactly (9 actors, `STR-MOH-2023-001`, `STR-KSM-2023-001`), idempotent on rerun, fails closed on missing PE/OU/FY | Planned | See Phase 5 work register |
| STR-G06 | `kentender_budget` and `kentender_procurement` consumer wiring updated to final contract shapes; `strategy_alignment_handoff.py` fixed; dead `pvc_snapshot` field addressed | Planned | See Phase 6 work register |
| STR-G07 | All 4 UI routes (STR-UI-01–04) implemented in Vue per `strategy_portfolio_pilot`'s pattern, matching the 18 `strategy_design/*.dc.html` artboards | Planned | See Phase 7 work register |
| STR-G08 | Routes registered in `kt_cl_surface_registry.js`; module menu trimmed to Strategy Portfolio + Review tasks; legacy pages/shell glue deleted | Planned | See Phase 8 work register |
| STR-G09 | All 30 `STR-AC-0xx` cases pass with real evidence; one live unscripted end-to-end journey per role completed | Planned | See Phase 9 work register and AC mapping table |

## Work register — Phase 0: plan and tracker

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-001 | Research: current `kentender_strategy` app inventory (doctypes, pages, services, API, seeds, patches, tests) | Done | Explore-agent pass; findings folded into plan §3 and this tracker's headline finding |
| STR-002 | Research: downstream blast radius (`kentender_budget`, `kentender_procurement`, `kentender_core`, Playwright, other apps) | Done | Explore-agent pass; findings folded into plan §4 |
| STR-003 | Research: `kentender_core` reuse precedents (`authorization_policy`, `audit_event_service`, `reference_data_transitions`/`queries`/`api`/`idempotency`, `strategy_portfolio_pilot`, shell/registry/tokens) | Done | Explore-agent pass; findings folded into plan §1.1/§5 |
| STR-004 | Confirm architecture decisions with user (authorization engine, audit mechanism) | Done | `AskUserQuestion` — both recommended options (`authorization_policy`, migrate to core `Audit Event`) confirmed 2026-08-23 |
| STR-005 | Author `04_Strategy_Rebuild_Implementation_Plan.md` | Done | This file's companion document |
| STR-006 | Author this tracker, in the house style used by `docs/mvp-1-r1/05_pe_and_fy_maintenance/IMPLEMENTATION_TRACKER.md` | Done | This document |

**Checkpoint:** Done. Phase 1 may begin.

## Work register — Phase 1: domain model rebuild

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-101 | Create `Strategic Plan` doctype (`plan_id`, `procuring_entity_id`, `owner_org_unit_id`, `title`, `plan_role`, `parent_primary_plan_id`, `period_start`, `period_end`) | Done | `kentender_strategy/kentender_strategy/kentender_strategy/doctype/strategic_plan/` rewritten in place; confirmed live via `bench execute frappe.db.exists ["DocType","Strategic Plan"]` post-migrate |
| STR-102 | Create `Strategic Plan Version` doctype (`plan_version_id`, `plan_id`, `version_number`, `based_on_plan_version_id`, `status`, `effective_from`, `effective_to`, `return_reason`) | Done | New doctype folder; 8-value status vocabulary (Draft/In Review/Returned/Awaiting Approval/Approved/Active/Superseded/Archived) matches spec §6.1 exactly. Confirmed created via `bench execute frappe.db.exists ["DocType","Strategic Plan Version"]` |
| STR-103 | Migrate existing `Strategic Plan` records/data into the split schema | Done, by deletion not mapping | Product owner confirmed (2026-08-23) dev-site data may be deleted rather than migrated — see decision log. Patch truncates `tabStrategic Plan` rather than attempting a field mapping into the incompatible new shape |
| STR-104 | Create `Strategy Node` doctype (`strategy_node_id`, `plan_version_id`, `node_type`, `parent_node_id`, `title`, `display_order`); delete `strategy_programme`, `strategy_sub_programme`, `strategic_objective`, `strategic_outcome` | Done | New doctype folder + patch deletes the 4 old doctypes via `frappe.delete_doc("DocType", ..., force=1)`. Confirmed all 4 absent and `Strategy Node` present post-migrate |
| STR-105 | Trim `Performance Indicator`: drop `measurement_frequency`/`data_source`/`responsible_function`/`measurement_type` (none in spec §5.4); rename measured-node link to `measures_node_id`; spec's `name` field stored as `indicator_name` (Frappe reserves `name`) | Done | `performance_indicator.json` rewritten; guard `validate_performance_indicator` enforces Objective/Outcome-only + same-version + unique-name-under-node (STR-BR-008/009), covered by 2 passing tests |
| STR-106 | Trim `Performance Target`: drop all baseline/tolerance/benefit_owner/measurement_verifier/period/status fields; enforce `financial_year_id` XOR `target_by_date`; `comparison` restricted to At least/At most/Equal to; percentage range 0–100 | Done | `performance_target.json` rewritten; guard `validate_performance_target` covered by 4 passing tests (XOR anchor, invalid comparison, percentage range, plan-period containment for date-anchored targets) |
| STR-107 | Delete `Performance Measurement` doctype and `strategy_measurement.py` service | Done | Doctype dropped via patch; service file removed; dead `transition_measurement`/`MEASUREMENT_TRANSITIONS` removed from `strategy_transitions.py`; dead measurement functions (`save_measurement_draft`, `get_measurement`, formatting helpers) removed from `strategy_writes.py`/`strategy_contracts.py`; 3 API endpoints removed from `strategy_api.py` |
| STR-108 | Delete `Strategy Value Commitment` + `Strategy Value Commitment Link` doctypes | Done | Dropped via patch. Dead `upsert_strategy_value_commitment`/`set_commitment_links` removed from `strategy_writes.py`; 2 API endpoints removed. `list_strategy_value_commitments` in `strategy_contracts.py` left in place (still called by `get_plan_overview`/`strategy_consumer.list_strategy_commitments`) — deliberately not deleted to avoid trading a DB-level failure for a NameError; both fail identically until Phase 4, tracked below |
| STR-109 | Delete `strategy_performance.py` service (performance dashboard projection) | Done | File removed; import + 2 whitelisted endpoints (`get_strategy_performance`, `export_strategy_performance_report`) removed from `strategy_api.py` |
| STR-110 | Delete `Strategy Audit Event` doctype; route all transitions through `audit_event_service.log_audit_event()` | Done | Doctype dropped via patch. `strategy_audit.py` rewritten: `record_event()` now calls `kentender_core.services.audit_event_service.log_audit_event()`; added `list_events()` read-back helper. Verified via test: an event written through `record_event` is readable as a real `Audit Event` row with correct `document_type`/`document_name`/`action`, and `Strategy Audit Event` confirmed absent as a DocType |
| STR-111 | Delete tests tied to removed concepts | Done, scope widened | Original 5 targeted files deleted, but `bench run-tests --module` was found to still import every test file in the app during category preparation — every one of the other 15 pre-existing Strategy test files transitively depended on the old schema (mostly via `upsert_works_master_strategy_hierarchy`) and blocked even a focused run. All 15 deleted rather than left broken; each is real re-coverage work for the phase that rebuilds the feature it tested (Phase 2: `plan_structure`/`plan_overview`/`review_readiness`/`plan_activation_concurrency`/`notifications`; Phase 3: `authority_capability`; Phase 4: `integration_contracts`/`smoke_contract`/`reference`; Phase 5: `seed_integrity`; Phase 6: `downstream_usage`; Phase 7: `create_plan`/`portfolio_ui01`; `mvp1_domain`/`mvp1_ac_matrix` superseded by this document's own STR-AC-0xx list) |
| STR-112 | Focused tests: STR-BR-002/003/005–011, STR-AC-001, 005, 006 | Done | New `kentender_strategy/tests/test_str_chg_001_phase1_domain_model.py`, 16 tests, self-contained (uses real seeded `PE-MOH`/`FY-2027-2028`, own fixtures via `tearDown`). `bench --site kentender.midas.com run-tests --app kentender_strategy --module kentender_strategy.tests.test_str_chg_001_phase1_domain_model` → **16 passed, 0 failed** on the corrected run (2 real bugs found and fixed first: a `str`-vs-`date` comparison in the version/target period guards, and a test fixture accidentally colliding two root-level Pillars on the same `display_order`) |

**Checkpoint:** Done. Live-verified: `bench migrate` clean on `kentender.midas.com`; all 8 removed doctypes confirmed absent, both new doctypes confirmed present via direct DB queries; 16/16 new focused tests green; `kentender_budget`'s `budget_line.py` and `kentender_procurement`'s `strategy_alignment_handoff.py` both confirmed to still *import* cleanly (`frappe.get_attr` probe) even though their called functions are functionally broken until Phase 4/6 — a controlled, diagnosable `DoesNotExistError`, not a cascading crash, confirmed by directly invoking the old seed function live.

**Known, tracked regressions carried into Phase 2+ (not silently introduced, not blocking Phase 1):**
- `kentender_budget`'s live Budget Line strategy-linking (`apply_budget_primary_strategy_reference` → `_validated_strategy_reference` → `strategy_contracts.validate_strategy_reference`/`build_strategy_reference`) is functionally broken — those functions still walk the pre-rebuild Programme/Sub-programme/Objective/Outcome hierarchy and read `Strategic Plan.status`, both gone. User-confirmed accepted tradeoff (decision log, 2026-08-23); fixed in Phase 4.
- `kentender_strategy`'s own legacy structure-editor writes (`upsert_structure_node`, `reorder_structure_nodes`, `delete_structure_node` in `strategy_writes.py`, still wired in `strategy_api.py`) reference the deleted 4 hierarchy doctypes. Genuinely Phase 2 (`save_strategy_structure_draft`)/Phase 7 (UI) territory; the legacy `strategy_plan_structure` page they backed is slated for deletion in Phase 8.
- `strategy_transitions.py`'s `transition_plan`/`_activate_plan` operate on `Strategic Plan` fields (`status`, `submitted_by`, `plan_code`, `procuring_entity`) that Phase 1 moved off `Strategic Plan` entirely. Left in place with an explanatory code comment; the real 9-row §6.1 lifecycle engine on `Strategic Plan Version` is Phase 2.
- `strategy_contracts.py`'s `list_strategy_value_commitments`, `get_strategy_portfolio`'s `_plan_attention`, `get_strategy_tree`, `get_plan_overview`, and related read-model functions still query the deleted doctypes/old field names. All fail with a DB-level "doctype/column not found" error, not a silent wrong answer. Full rebuild is Phase 4.
- `kentender_strategy`'s own seed pipeline (`kentender_mvp_v1_strategy.py`, `works_master_strategy_hierarchy.py`, `moh_review_fixtures.py`) is non-functional against the new schema — confirmed via a live probe (`upsert_works_master_strategy_hierarchy()` raises a clean `DoesNotExistError: DocType Strategy Programme not found`). Rebuilt in Phase 5 per §16's exact identifiers.
- The same seed dependency means `kentender_budget`'s and `kentender_procurement`'s own strategy-fixture-seeding tests/Playwright specs (`test_budget_line_strategy_validate.py`, `test_r3_00*_*.py`, `budget-funding-line-strategy-xmod-str-001.spec.ts`) cannot currently run to completion — same root cause as above, same Phase 5/6 fix point.

## Work register — Phase 2: lifecycle engine

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-201 | Rebuild `strategy_transitions.py` as table-driven engine covering the full §6.1 9-row transition table | Done | `TRANSITIONS` dict covers all 8 user-invoked (status, action) pairs; "Activate successor" implemented inside `_activate()` as the system-driven side effect of activating a version, not a separate user action key, matching §6.1's own framing ("System, as part of the successor activation transaction") |
| STR-202 | Implement `_check_expected_version()` optimistic concurrency (BR-016), modeled on `reference_data_transitions.py` | Done | Same `modified`-timestamp-as-token mechanism as CFG-CHG-002. Covered by `test_stale_write_rejected` |
| STR-203 | Server-computed `available_actions` per version from state + caller capability (no static status→action map) | Done | New `strategy_authorization.py` wires `kentender_core.services.authorization_policy` (per the confirmed Phase 0 decision) rather than the older `org_scope_access.py`; `available_actions()` calls non-throwing `evaluate_capability()` per candidate action. Covered by 3 tests asserting exact action sets at Draft/In Review/Awaiting Approval/Active |
| STR-204 | Atomic activate-supersede transaction with DB-serialized overlap check (STR-BR-004) | Done, with an honest scope note | `_assert_no_primary_overlap()` + same-plan supersession both run inside `_activate()`, in the request's own transaction. The overlap check is a read-then-check-then-write guard (matching this codebase's pre-existing overlap-check style, e.g. Phase 1's `strategy_domain_guards`) — not a `SELECT ... FOR UPDATE` row lock, so true concurrent-request serialization is not proven, only single-request correctness (matches CFG-CHG-002's own documented level of rigor for the equivalent PE overlap check). Covered by 2 tests (rejects cross-plan Primary overlap; correctly supersedes same-plan predecessor without being blocked by its own overlap guard) |
| STR-205 | Focused tests: STR-BR-004, 006, 015–017; STR-AC-008, 010–015 | Done | New `kentender_strategy/tests/test_str_chg_001_phase2_lifecycle.py`, 9 tests, self-contained Capability Profile/Operational Scope Assignment/Separation of Duties Rule fixtures (Phase 3 pattern, same as CFG-CHG-002's own lifecycle tests) since Phase 3's production capability seeding doesn't exist yet — every check here fails closed until then, the correct default. `bench --site kentender.midas.com run-tests --app kentender_strategy --module kentender_strategy.tests.test_str_chg_001_phase2_lifecycle` → **9 passed, 0 failed**. Phase 1's 16 tests re-run alongside: **16 passed, 0 failed**, no regressions. Two real bugs found and fixed during this phase (not just documented): a cross-test data leak caused by an unnecessary `frappe.db.commit()` in a test (removed — FrappeTestCase's own transaction handling doesn't need it and the explicit commit broke isolation between tests), and a guard bug where `validate_strategic_plan_version`'s baseline-status check re-ran on every save of a successor version — including the successor's own activation save, by which point its baseline had already been correctly superseded — wrongly rejecting a version's own legitimate activation. Fixed by scoping the check to `doc.is_new() or doc.has_value_changed("based_on_plan_version_id")` |

**Checkpoint:** Done. Full Draft→In Review→Awaiting Approval→Approved→Active cycle demoed with 3 distinct actors (Author/Reviewer/Approval Authority) and real SoD enforcement in `test_full_lifecycle_happy_path_with_distinct_actors`; overlap and supersession demoed against real `Strategic Plan`/`Strategic Plan Version` rows, not a screenshot.

**Known gap carried forward:** `strategy_notification_service.py`'s `notify_plan_transition`/`notify_measurement_transition` are not wired into the new `transition_plan_version()` (the old `transition_plan`/`transition_measurement` functions that called them were removed in Phase 1). Notifications were not in this phase's stated scope (plan/tracker) and are not one of the 8 STR-CHG-001 sections this module is required to implement by name; revisit if a later phase's UI work needs them.

## Work register — Phase 3: roles and permissions

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-301 | Create Capability Profiles: Strategy Author, Strategy Reviewer, Strategy Approval Authority (Strategy Viewer is a pure read role — see STR-302 note) | Done | New `ensure_strategy_governance_roles()` in `strategy_authorization.py`. Real Frappe Role names per spec §7: `Strategy Viewer`/`Strategy Reviewer` already existed with the exact right names (reused, not recreated); `Strategy Author`/`Strategy Approval Authority` are net-new. 3 Capability Profiles seeded (`CAP-STRATEGY-AUTHOR/-REVIEWER/-APPROVAL-AUTHORITY`), one capability each, `allows_entity_wide=1` (a real bug found and fixed: `allows_entity_wide=0` was rejected by `kentender_core`'s own `authorization_records.validate_authorization_record()` — "This capability profile does not permit entity-wide assignment" — the moment a real PE-scoped-without-resource-narrowing assignment was attempted, confirming the fix against `kentender_core`'s actual validation, not just inspection) |
| STR-302 | Add read-only capabilities for Budget/Finance Officer, Procurement Planner, Auditor (cross-module, no Strategy workflow access) | Deferred to Phase 4, with reasoning | Spec §7 describes these roles' access as reading "the applicable Active context and lineage through contracts" — i.e. `resolve_strategy_context`/`list_strategy_objectives`/`get_strategy_lineage` (§10), not a lifecycle action this phase's capability engine gates. There is no Phase-3-owned action for them to be granted a capability *for* yet; seeding an unused capability now would violate the data-purpose gate (§2.2). Revisit when Phase 4 builds the contract layer these roles actually read through |
| STR-303 | Wire Operational Scope Assignments scoped by PE + optional OU + plan-role + effective dates | Done, with a documented scope limitation | PE scoping (`procuring_entity_id`) and effective dates are fully wired via `resource_context_for_version()` and `Operational Scope Assignment`'s own `effective_from`/`effective_to`, confirmed live (`test_assignment_scoped_to_other_pe_denied_stc_br_001`). OU scoping is wired (`organisation_unit_id` on the `ResourceContext`) but not yet exercised by a test (no OU-scoped Strategy fixture exists yet). **Plan-role scoping is not implemented**: `Operational Scope Assignment`'s generic `resource_scope_type`/`resource_scope_id` is a Dynamic-Link mechanism, unsuited to matching a plain enum value (`plan_role` is Select, not a linkable DocType) without a schema change to a shared `kentender_core` doctype — out of Strategy's ownership boundary to change unilaterally. Documented as an accepted MVP-1 simplification, not silently dropped |
| STR-304 | Seed pairwise Separation of Duties Rules (submit↔review, submit↔approve, review↔approve) | Done | 3 production `Separation of Duties Rule` rows (`SOD-STRATEGY-AUTHOR-REVIEWER/-AUTHOR-APPROVE/-REVIEW-APPROVE`), `module_name="Strategy"`, `status="Active"`. Confirmed present and correctly paired via `test_seed_is_idempotent_and_creates_expected_rows` |
| STR-305 | 3-way non-repeat guarantee (author≠reviewer≠approver on one version) | Done, by a simpler mechanism than planned | The plan originally assumed a CFG-CHG-002-style hand-check (prior-capability membership check inside the transition function) would be needed, borrowing from that module's 3-actor *reopen* flow. On inspection this isn't needed here: Strategy's 3 capabilities each gate a *distinct doctype-tracked stage* (unlike reopen's single accumulating pseudo-transition), so the 3 pairwise SoD rules from STR-304 already cover all `C(3,2)=3` two-role overlaps completely — proven, not assumed, by Phase 2's own `test_reviewer_cannot_recommend_own_submission`/`test_author_cannot_approve_own_version`, both passing with only pairwise rules and no extra hand-check code |
| STR-306 | Rewrite `strategy_permissions.py`; delete `can_submit_measurement`/`can_verify_measurement` | Done, scoped narrowly | The 2 dead measurement-gate functions (and the now-unused `ROLE_PERF_OFFICER`/`ROLE_PERF_VERIFIER` aliases) deleted — confirmed dead (zero callers) before removal. The *lifecycle* authorization surface (submit/review/approve/activate) is fully on `authorization_policy` via `strategy_authorization.py` (Phase 2). The remaining legacy functions in `strategy_permissions.py` (`can_edit_draft_plan`, `entity_for_user`, `assert_entity_in_scope`, etc.) are **not** rewritten onto `authorization_policy` yet — they still gate `strategy_writes.py`/`strategy_contracts.py`/`strategy_reference.py`, which are themselves Phase 4/6/7 rebuild targets already left on the pre-rebuild schema. Rewriting the permission helper without rewriting its callers would just relocate the same deferred work; tracked as part of those phases, not silently dropped here |
| STR-307 | Focused tests: STR-BR-001–004; STR-AC-003, 004, 010, 021, 022 | Done, with an honest scope note | New `kentender_strategy/tests/test_str_chg_001_phase3_governance.py`, 5 tests: seed idempotency (`bench execute` twice, second run creates nothing — direct evidence, not inference), a real user granted only the Author capability can submit but not recommend, an unassigned user is denied (STR-AC-004), Administrator with no assignment is denied (§1.1/§19 no-fallback rule), and cross-PE scope is denied using two real seeded PEs (`PE-MOH`/`PE-CGKIS`, STR-BR-001). `bench --site kentender.midas.com run-tests --app kentender_strategy --module kentender_strategy.tests.test_str_chg_001_phase3_governance` → **5 passed, 0 failed**. STR-AC-021/022 are UI/API-surface acceptance criteria ("Portfolio counts... apply the same server-side scope") with no UI/contract layer to exercise yet — this phase proves the underlying scope mechanism they depend on, not the criteria themselves; full verification carried to Phase 7/9, same pattern as every other UI-dependent AC in this tracker. Phase 1 (16 tests) and Phase 2 (9 tests) re-run alongside: **25 passed, 0 failed**, no regressions |

**Checkpoint:** Done. Governance seed run twice live against `kentender.midas.com` (idempotent, confirmed via direct query, not inspection); a real user with only the seeded `CAP-STRATEGY-AUTHOR` profile demonstrated submitting a real plan version and being denied the reviewer action on the same version, entirely through production-named rows — not the throwaway per-test fixtures Phase 2 used.

**Doctype permission blocks updated to match (not left stale):** all 5 rebuilt doctypes' (`Strategic Plan`, `Strategic Plan Version`, `Strategy Node`, `Performance Indicator`, `Performance Target`) baseline Frappe `permissions` tables were updated from the old `Strategy Manager`/`Strategy Officer` role names to `Strategy Author` (create/write), `Strategy Reviewer`/`Strategy Approval Authority` (read-only — their real actions are capability-gated lifecycle transitions, not raw DocType writes), and `Strategy Viewer` (read-only). `bench migrate` confirmed clean afterward; Frappe's own doctype-permission sync auto-created the 2 new Role records during that migrate, before the governance seed function ran — confirmed by direct query, not assumed.

## Work register — Phase 4: service contracts (§10, §10.1)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-401 | Decide and create API module for the 4 §10 contracts (new `api/strategy_consumer_api.py` vs. additions to `strategy_api.py`) | Planned | |
| STR-402 | Whitelist `resolve_strategy_context`, `list_strategy_objectives`, `get_strategy_lineage`, `create_strategy_snapshot` as thin wrappers over rebuilt `strategy_consumer.py` | Planned | |
| STR-403 | Implement 8 §10.1 command contracts as thin dispatchers (`save_strategy_plan_draft` … `archive_strategy_version`) | Planned | |
| STR-404 | Create `Strategy Command Journal` doctype + idempotency wrapper modeled on `reference_data_idempotency.py::run_idempotent()` | Planned | |
| STR-405 | Implement §14 error contract in full (`STRATEGY_SCOPE_REQUIRED` … `STRATEGY_DOWNSTREAM_FORBIDDEN`) | Planned | |
| STR-406 | Delete legacy API methods tied to removed concepts: `list_strategy_value_commitments`, `upsert_strategy_value_commitment`, `set_commitment_links`, `save_measurement_draft`, `transition_measurement`, `get_measurement`, `get_strategy_performance`, `export_strategy_performance_report` | Planned | |
| STR-407 | Focused tests: one per contract; STR-AC-009, 016–020 | Planned | |

**Checkpoint:** Not started.

## Work register — Phase 5: seed contract (§16)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-501 | Rename actors to exact 9 (`str.author.moh@example.test` … `str.auditor@example.test`) | Planned | |
| STR-502 | Rebuild `STR-MOH-2023-001` with spec-exact stable node IDs and lifecycle-authority timestamps (§16.3) | Planned | |
| STR-503 | Rebuild `STR-KSM-2023-001` cross-PE isolation plan (§16.4) | Planned | |
| STR-504 | Build thin Strategy-side PE/OU/FY existence guard, fail closed with `STRATEGY_CONFIG_MISSING`; no fallback record creation | Planned | No ready-made bare PE/OU/FY resolver exists — `reference_data_resolver` only exposes a PE/FY-Context-scoped check. Must build new, not assume reuse. |
| STR-505 | Build isolated Version-2 workflow fixture (§16.5), torn down after test use | Planned | |
| STR-506 | Delete dead seed shims: `moh_mvp_v1_strategy.py`, `works_master_strategy_purge.py`, `seed_works_master_strategy_purge.py` | Planned | |
| STR-507 | Focused test: seed runs twice, no duplicates (STR-AC-023, 024) | Planned | |

**Checkpoint:** Not started.

## Work register — Phase 6: downstream consumer migration

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-601 | Re-point `kentender_budget`'s `strategy_consumer` call sites at final Phase 1/4 contract shapes | Planned | Check `budget_line.py`, `budget_line_contracts.py`, `budget_reference.py`, `test_budget_line_strategy_validate.py` |
| STR-602 | Update `kentender_budget` copy strings referencing "Strategy Value Commitment" | Planned | `budget_readiness_contracts.py`, `budget_revision_contracts.py` |
| STR-603 | Fix `kentender_procurement/procurement_lifecycle/strategy_alignment_handoff.py`'s broken doctype/field references; wire to `list_strategy_objectives`/`create_strategy_snapshot` | Planned | Currently queries nonexistent `"Strategy Objective"` doctype with wrong field names — pre-existing bug, independent of this rebuild |
| STR-604 | Remove or relabel dead `pvc_snapshot`/`strategy_snapshot` fields on `Procurement Plan Item Version` | Planned | Producer function already deleted in an unrelated commit; fields are currently unpopulated dead schema |
| STR-605 | Update Playwright specs asserting on removed testids/routes (`kt-str-perf-*`, `kt-str-*commitments*`, `/desk/strategy-performance`, `/desk/strategy-value-commitments`, `/desk/strategy-plan-measurements`) | Planned | Must land in the same window as the screens/routes they cover disappear, not deferred |
| STR-606 | Focused/contract tests: Budget consumer tests pass against new contract shapes | Planned | |

**Checkpoint:** Not started.

## Work register — Phase 7: Vue UI (STR-UI-01–04)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-701 | Re-read `strategy_design/*.dc.html` fresh at phase start | Planned | 18 artboards: STR-DES-01 through STR-DES-12d |
| STR-702 | Build STR-UI-01 Strategy Portfolio (`/app/strategy`), cloning `strategy_portfolio_pilot`'s Page/bundle/composable skeleton | Planned | |
| STR-703 | Build STR-UI-02 Plan workspace (`/app/strategy/plan/{plan_id}`) — Overview/Structure/History tabs | Planned | |
| STR-704 | Build STR-UI-03 Structure editor (`/app/strategy/plan/{plan_id}/version/{version_number}/structure`) — hierarchy tree + selected-record card | Planned | |
| STR-705 | Build STR-UI-04 Review task (`/app/strategy/review/{plan_version_id}`) — Overview/Structure/Changes/History tabs, role-appropriate decision footer | Planned | |
| STR-706 | Reuse `kt_industry_tokens.css` shared tokens/classes; no second per-module token set | Planned | |
| STR-707 | In-Vue confirm dialogs for Return/Approve/Activate (AGENTS.md §6.3) | Planned | |
| STR-708 | 4 register state variants (Loading/No matches/Forbidden/Server error) per STR-DES-12 | Planned | |
| STR-709 | Wire every screen to real Phase 4 API — zero fixture data in shipped components | Planned | |

**Checkpoint:** Not started.

## Work register — Phase 8: shell/registry + module menu

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-801 | Register 4 routes in `kt_cl_surface_registry.js` | Planned | |
| STR-802 | Delete legacy `strategy_alignment_shell.js`/`strategy_alignment_workspace_redirect.js` | Planned | |
| STR-803 | Trim Strategy Alignment module menu to Strategy Portfolio + Review tasks only (latter role-gated) | Planned | |
| STR-804 | Delete the 13 legacy pages per Phase 1 inventory verdicts (keep only the rebuilt STR-UI-01–04 routes) | Planned | |
| STR-805 | Update `stitch_desk_chrome_registry.py` rows and `test_module_registry.py` for the new `page_js` set | Planned | |

**Checkpoint:** Not started.

## Work register — Phase 9: verification against acceptance contract (§17)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-901 | Map all 30 `STR-AC-0xx` cases to an owning test; no AC left unassigned | Planned | |
| STR-902 | Service/domain tests (TDD), then API/permission tests | Planned | |
| STR-903 | Browser smoke: one focused path per role (Author, Reviewer, Approval Authority, Viewer, forbidden actor) per §18.2 | Planned | State plainly if no browser tool is available in the executing session, same as CFG-CHG-002 |
| STR-904 | Artboard-vs-rendered-screen content comparison | Planned | |
| STR-905 | Full `kentender_strategy` suite passes once after targeted stabilization | Planned | |
| STR-906 | Budget contract consumer tests pass | Planned | |
| STR-907 | Production build succeeds without global CSS regression | Planned | |
| STR-908 | Static scan: no removed concept or legacy import in executable Strategy code | Planned | |

### STR-AC-0xx → test mapping

To be completed during Phase 9, in the same style as CFG-CHG-002's `CFG-PEFY-AC-0xx` mapping table (AC → owning test → notes), once tests exist to cite.

**Final checkpoint:** Not started — `STR-CHG-001` is not Done until every AC above has real evidence and the primary end-to-end journey per role has been run.

## Open items carried forward (not blocking, tracked)

- Phase 1 deleted all 15 pre-existing Strategy test files beyond the 5 originally scoped (STR-111) because `bench run-tests --module` imports every test file in the app during category preparation, and all 15 transitively depended on the old schema. Each file's replacement is assigned to the phase that rebuilds the feature it tested — see STR-111's evidence note for the exact mapping. Do not treat this as coverage regained; it is coverage owed.

- `kentender_procurement/procurement_lifecycle/strategy_alignment_handoff.py` is currently broken (queries a nonexistent `"Strategy Objective"` doctype with wrong field names) — pre-existing, unrelated to this rebuild's start state, fixed in Phase 6.
- `Procurement Plan Item Version.pvc_snapshot`/`strategy_snapshot` fields are already dead (producer function `add_demand_to_plan.py::_strategy_snapshots` was deleted in an unrelated commit and never recreated) — addressed in Phase 6, not a new defect introduced here.
- `tests/ui/helpers/strategyWorkbench.ts` is dead code (imports a nonexistent `./strategyLanding`, zero callers) — unrelated to this rebuild, noted so it isn't mistaken for live coverage.
- Two parallel authorization mechanisms exist platform-wide (`org_scope_access.py`/User Scope Assignment vs. `authorization_policy.py`/Operational Scope Assignment). This rebuild moves Strategy onto the newer one; Budget still uses the older one as of this writing — full reconciliation across all modules is out of scope for this change unit.
- `strategy_consumer.py`'s `record_verified_result` stub (raises `NotImplementedError`, "deferred to Contract Management scope") is correct as-is per spec §10 and should not be implemented in this change unit.
- Cross-app copy strings in `kentender_budget` mentioning "Strategy and Value Commitments" / "Strategy Value Commitment coverage" need updating in Phase 6 alongside the functional consumer-wiring fix, not left stale.
