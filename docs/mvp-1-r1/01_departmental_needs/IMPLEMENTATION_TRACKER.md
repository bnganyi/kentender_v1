# NDS-CHG-001 v1.1 — Departmental Needs rebuild — tracker

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1.1.md` (approved 28 Aug 2026).
**Companions:** `02_NDS_Rebuild_Gap_Analysis.md`, `03_NDS_Rebuild_Implementation_Plan.md`.
**Status:** Phase 0 complete. Phase 1 complete (schema landed, clean migrate, 25/25 domain tests green). **Phase 2 complete** (full §5.1/§5.2/§5.3 command set, 39/39 lifecycle tests green; DEBT-04 closed). Phases 3–10 not started. Four carried debts remain, the largest being that the UI is dark until Phase 7.
**Started:** 2026-08-29

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence (a command, a test name, a diff, a described screenshot) — not "looks right."
3. If a touched file still references a concept §1.1 or §17 prohibits (item child table, attachment, `indicative_cost`, `currency`, `delivery_or_use_location`, `other_unit`, `business_justification`, `Partially included`, `Departmental Review Delegate`, `Needs Configuration Manager`, a legacy `/demands` route, a custom capability store), the row that touches it is not `Done`.
4. No row may introduce an alias, redirect, dual-write, compatibility shim, or parallel legacy+Vue screen. If one appears, treat it as a defect in that row, not a valid completion.
5. §11 (Claude Design contract) governs visual/content fidelity only. §1–10 and §12–20 govern behaviour. A row implementing behaviour from §11 content instead of §12 is a defect, not a shortcut.
6. Deletion lands in the same phase as its replacement. "Delete later" is not a valid row state.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-08-29 | Treat this as a full rebuild in place, not a `business_justification` rename patch | The v1.0→v1.1 doc diff is small, but §1.1's disposition register (unchanged since v1.0) is largely unimplemented: item child table, attachments, cost/currency, location, free-text unit, `Partially included`, extra roles and the entire successor/withdrawal-decision lifecycle all diverge. See `02_NDS_Rebuild_Gap_Analysis.md` §3. |
| 2026-08-29 | **FIRM (Project Owner, 2026-08-29) — D1 owning app.** Departmental Needs and Procurement Planning remain **separate modules within `kentender_procurement`**. Planning consumes Accepted Needs **only** through the published handoff contract. Direct access to Departmental Needs DocTypes, tables or internal services is **prohibited** and **enforced by automated architecture tests**. No additional Frappe app is introduced. | Owner decision. Avoids a large, low-value app migration mid-MVP while keeping §3's ownership boundary real rather than conventional: the prohibition is executable (NDS-901/NDS-910), not documentary. This closes the open question raised in `02_NDS_Rebuild_Gap_Analysis.md` §10.1. |
| 2026-08-29 | Adopt **native Frappe** Role/DocType permission/User Permission for this module (D2) | §6 and NDS-AC-044 mandate it explicitly. **This diverges from CFG-CHG-002 and STR-CHG-001**, which both adopted `kentender_core.services.authorization_policy`. Recording the divergence so the platform-level split stays visible rather than being silently resolved in either direction. |
| 2026-08-29 | ~~`DepartmentalNeedReviewTask` as a typed projection over core's `Workflow Task` (D3)~~ **REVERSED during Phase 1** — built as a module-local `Departmental Need Review Task` doctype instead | The original decision was made before reading `kentender_core/services/workflow_tasks.py`. That engine calls `require_capability()` / `evaluate_capability()` internally on every `execute_routed_transition` and `transition_task`, so reusing it would have kept Departmental Needs bound to the capability store that §6 and NDS-AC-044 prohibit — and that the Project Owner directed against on 2026-08-29. §4.4 specifies `DepartmentalNeedReviewTask` as a first-class entity in any case, so the module-local doctype is both the literal spec reading and the only one compatible with native permissions. |
| 2026-08-29 | **Phase 2 — the root state does not move during the §5.2 successor lifecycle.** A Need with an open successor stays `Accepted for planning` from Create update through Return/Accept/Decline; the successor's own `version_status` carries its state. | §5.2 says explicitly that the earlier accepted version "remains effective" for every outcome except Accept. If the root moved to `Submitted` or `Returned` while a successor was under review, the Need would stop presenting as accepted and Planning's source contract would read as unavailable — contradicting the same table. The version-level status is the only place the successor's state can live without disturbing the accepted source. |
| 2026-08-29 | **Phase 2 — a Draft/Submitted Plan allocation is not a withdrawal blocker.** The `NDS_ACTIVE_PLAN_DEPENDENCY` check counts only `Effective` allocations on the exact accepted version. | §5.3 states it directly: "A Draft or Submitted DPP is not an Active Plan dependency; withdrawal may proceed and Planning will receive a stale/ineligible-source event." The inherited code blocked on Draft allocations too, which would have deadlocked withdrawal behind Planning drafts the requester cannot see or influence. NDS-BR-016 supplies the exact-version scoping. |
| 2026-08-29 | **Phase 2 — the scope check runs before maker-checker.** An author with no Head of User Department role attempting a decision gets `NDS_SCOPE_DENIED`, not `NDS_MAKER_CHECKER`. | §9 requires `NDS_SCOPE_DENIED` to "disclose no protected record data". Telling a user without review authority that they are the *maker* of a specific record confirms the record exists and that they authored it. Maker-checker is reachable only for someone who actually holds review authority — which is the case NDS-AC-010 describes. Both orderings are tested. |
| 2026-08-29 | `DepartmentalNeedVersion` as a standalone doctype, not a child table (D4) | Review tasks, decisions, events and Planning lineage all reference a version by its own stable ID; a child table cannot carry that identity. |
| 2026-08-29 | Rebuild fixtures rather than migrate existing rows (D6) | §1.1 prohibits legacy migration/compatibility. Live rows here are seed/test data. **Must be confirmed against the target site before any drop.** |

## Headline findings (read before touching code)

1. **The code was built against a spec that no longer exists.** `services/notifications.py:1`, `services/attachments.py`, `departmental_needs_create_page.js:191` and `kt_cl_surface_registry.js` cite `NDS-CHG-002`; there is no such document in `docs/`. `departmental_needs_create_page.js:191` also cites an "NDS-CHG-002 Phase 9 coverage map" that exists nowhere in the repo.
2. **`services/lifecycle.py` is the asset worth keeping.** Its transactional pattern (idempotency key → `SELECT … FOR UPDATE` → optimistic token → authorization → state guard → validation → mutate → audit with before/after hashes → routed task dispatch) is sound and spec-aligned. Reuse the pattern; replace what it operates on.
3. **Roughly half the specified screens do not exist**, and the ones that do are vanilla-JS Frappe Desk pages, not Vue-in-Desk. `request_withdrawal` is reachable from no screen at all; withdrawal review tasks have no UI.
4. **`target_financial_year` is a plain `Data` string**, not a Link — a real defect independent of this rebuild.
5. **The existing test suite is thorough but tests the wrong model** (including attachments and delegate review, both now prohibited). It is a rewrite, not an extension.
6. `design/uploads/…v1.1.md` is a stale **pre-approval draft** (`Status | Proposed for approval`). Not authority.

## Carried debts opened by Phase 1 (must close before their named phase is Done)

| ID | Debt | Closes in | Detail |
|---|---|---|---|
| DEBT-01 | **The Departmental Needs screens are non-functional.** The five legacy jQuery pages still call the pre-v1.1 API shape (`target_financial_year`, `items`, `business_justification`, attachment endpoints) and render fields that no longer exist. | Phase 7 | Accepted deliberately: §1.1/§17 forbid a compatibility layer, and the schema change cannot land without breaking the old surface. Backend, seed and tests are green; only the UI is dark. |
| DEBT-02 | **Test coverage regressed.** 8 test modules that exercised the retired model were deleted rather than shimmed: attachments, audit hardening, completeness gaps, coverage gaps, gate01-03, notifications, submission validation, plan-need-allocation, UI contract. | Phase 9 | Their behaviours must reappear in the §15.1 layers (NDS-902…907). Specifically owed: maker-checker self-review block, resubmission revision integrity, §8.4 audit-field capture, multi-context selection, stale-token rejection, idempotent replay, cross-PE/OU isolation, notification recipients, every `_validate_submission` rejection path, allocation usage projection. The deleted `test_departmental_needs_ui_contract.py` asserted `/desk/departmental-needs` **and explicitly forbade** `/app/departmental-needs` — the inverse of §10; its replacement must assert the canonical routes. |
| DEBT-03 | **Planning still reads Departmental Needs tables directly**, violating the firm D1 boundary. | Phase 5 | `procurement_planning/services/need_allocations.py` and `plan_need_allocation.py` query `Departmental Need` / `Departmental Need Version` directly. Both carry an explicit boundary note. NDS-910 fails until they go through the published handoff contract. |
| ~~DEBT-04~~ | ~~**`Departmental Need Decision.workflow_task`** still links to core's `Workflow Task` and is always written as `None`.~~ | **Closed in Phase 2** | Field repointed to `review_task` → `Departmental Need Review Task` and now actually written by every task-bearing command. Orphan column dropped by `patches/nds_chg_001_v11_decision_review_task.py`, which fails closed if any row carried a value. Test `test_every_decision_records_the_review_task_that_authorised_it`. |
| DEBT-05 | Seed identifiers differ from §14: live OUs are `MOH-DIR-DHP` / `MOH-DIR-HRMD` (spec: `OU-MOH-DHI` / `OU-MOH-HRMD`). *(The intake-window half of this debt was closed in Phase 2 — see NDS-211.)* | Phase 6 | Following the CFG-CHG-002 `PE-CGKIS` precedent, live Configuration & Governance identifiers are authoritative; reconcile or accept explicitly. |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| NDS-G00 | Gap analysis, plan and tracker authored; stale upload draft reconciled | Done | `02_NDS_Rebuild_Gap_Analysis.md`, `03_NDS_Rebuild_Implementation_Plan.md`, this document |
| NDS-G01 | Schema matches §4 exactly; prohibited fields/doctypes absent; clean `bench migrate` | Done | Clean whole-site `bench --site kentender.midas.com migrate`. Post-migrate the module holds exactly the six §4 doctypes (Departmental Need, Departmental Need Version, Departmental Need Review Task, Departmental Need Decision, Need Withdrawal Request, Needs Intake Window); all three retired doctypes absent; `Departmental Author` present and both retired roles gone; 25/25 domain tests pass |
| NDS-G02 | All §5.1/5.2/5.3 transitions traversable; every §8.2 command exists with §9 codes | Done | Every row of the §5.1, §5.2 and §5.3 tables is traversed by `tests/test_departmental_needs_lifecycle.py` — **39 tests, 39 passed** (`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.test_departmental_needs_lifecycle`, 5.9s). Phase 1's 25 domain tests still pass. Codes asserted: `NDS_INTAKE_NOT_OPEN`, `NDS_FIELD_REQUIRED`, `NDS_MAKER_CHECKER`, `NDS_SCOPE_DENIED`, `NDS_STATE_CONFLICT`, `NDS_STALE_WRITE`, `NDS_OPEN_SUCCESSOR_EXISTS`, `NDS_WITHDRAWAL_ALREADY_OPEN`, `NDS_ACTIVE_PLAN_DEPENDENCY`, `NDS_CONTEXT_REQUIRED`. The §8.2 *names* land in Phase 4 (NDS-401) |
| NDS-G03 | Native Frappe permissions only; 5 roles exactly; acting HoD via scoped User Permission | Planned | |
| NDS-G04 | All §8.1/§8.2 contracts whitelisted; full §9 error contract returnable | Planned | |
| NDS-G05 | `DepartmentalNeedAccepted.v2` + Superseded/Withdrawn events; no downstream table query | Planned | |
| NDS-G06 | §14 seed contract satisfied incl. KEBS profile; idempotent on rerun | Planned | |
| NDS-G07 | All 8 routes/screens live in Vue, artboard-faithful, real API, no fixture data in shipped code | Planned | |
| NDS-G08 | Module menu/registry wiring correct; clean whole-site migrate | Planned | |
| NDS-G09 | §15.1 six-layer coverage green; static scan proves prohibited concepts absent | Planned | |
| NDS-G10 | All 45 ACs evidenced; §19 conformance checked; live browser walkthrough passed | Planned | |

## Work register — Phase 0: gap analysis, plan and tracker

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-001 | Diff NDS-CHG-001 v1.0 → v1.1 (spec + 9 modified artboards + 2 new 00_common docs) | Done | `02_NDS_Rebuild_Gap_Analysis.md` §2; old spec read at `git show d200ed4:…v1.0.md` |
| NDS-002 | Map current implementation (doctypes, services, API, workflow, screens, tests) | Done | `02_NDS_Rebuild_Gap_Analysis.md` §4–8 |
| NDS-003 | Cross-check every §1.1 disposition-register row against live code | Done | `02_NDS_Rebuild_Gap_Analysis.md` §3 — all 24 register rows, each with a verdict and file evidence |
| NDS-004 | Author plan and tracker in the house style used by `05_pe_and_fy_maintenance/IMPLEMENTATION_TRACKER.md` | Done | `03_NDS_Rebuild_Implementation_Plan.md`, this document |
| NDS-005 | Reconcile the stale `design/uploads/…v1.1.md` pre-approval draft | Planned | Confirmed stale (differs from approved copy only in `Status` line and §20 wording). Removal/reconciliation not yet performed — needs owner confirmation that the canvas does not depend on it |

## Work register — Phase 1: domain model

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-101 | Create `Needs Intake Window` doctype (§4.1); unique per PE/FY; derived Scheduled/Open/Closed | Done | `doctype/needs_intake_window/`. Controller enforces `closes_at > opens_at` and one window per PE/FY; no stored status field. Tests `test_intake_window_requires_close_after_open`, `test_only_one_intake_window_per_pe_and_financial_year` |
| NDS-102 | Create `Departmental Need Version` doctype (§4.3) with the six user values + version metadata + `content_hash` | Done | `doctype/departmental_need_version/`. Bounds enforced: title 5–160, description/expected result 10–1,000, quantity >0 ≤3dp. Immutability guard on any non-Draft status. 8 tests incl. `test_submitted_version_content_is_immutable`, `test_version_holds_the_six_requester_values` |
| NDS-103 | Create `Need Withdrawal Request` doctype (§4.6) incl. `Awaiting planning clearance` | Done | `doctype/need_withdrawal_request/`. 4-value status, reason 20–1,000, one open request per Need. Tests `test_only_one_open_withdrawal_request_per_need`, `test_withdrawal_reason_bounds_are_enforced` |
| NDS-104 | Slim `Departmental Need` to the §4.2 root; add version pointers; `record_version`; FY as a real Link | Done | 17 fields → 9. Dropped `title`, `business_justification`, `required_by_date`, `delivery_or_use_location`, `indicative_cost`, `currency`, `revision_no`, `submitted_by`, `pe_fy_context`, `submitted_at`, `last_decision_at`. Added `current_version`, `current_accepted_version`; `concurrency_token`→`record_version` (Int); `target_financial_year` Data → `financial_year` **Link**. Author is now the framework `owner` (§4.2). Tests `test_root_carries_no_prohibited_or_content_field`, `test_root_scope_is_immutable` |
| NDS-105 | Delete `Departmental Need Item` doctype and every reference | Done | `git rm` of the doctype; patch `nds_chg_001_v11_drop_retired_need_doctypes` drops the table. Consumers updated: `services/{lifecycle,workspace,usage}.py`, `procurement_planning/services/need_allocations.py`, `plan_need_allocation` (link repointed to `departmental_need_version`). Verified by grep: zero remaining `.py` references outside the test asserting absence |
| NDS-106 | Delete `Departmental Need Attachment` doctype and every reference | Done | Doctype, `services/attachments.py` (237 lines), its 4 API endpoints and `test_departmental_needs_attachments.py` all removed. Attachment scan-status gate removed from submission validation |
| NDS-107 | Split `Departmental Need Review` into the §4.5 decision record; retain idempotency ledger | Done | New `Departmental Need Decision` (immutable-on-save, unique `idempotency_key`, reason required only for the 6 §4.5 actions). Old doctype dropped by patch. Tests `test_decision_is_immutable_once_recorded`, `test_return_requires_a_reason`, `test_accept_collects_no_reason`, `test_idempotency_key_is_unique` |
| NDS-108 | Rename role `Departmental Need Requester` → `Departmental Author`; delete `Departmental Review Delegate` | Done | Pre-model-sync patch `nds_chg_001_v11_departmental_author_role` — creates the role, carries over existing holders, then deletes both retired roles with their `Has Role`/DocPerm rows. Verified post-migrate: only `Departmental Author` remains of the three |
| NDS-109 | Rewrite `setup/departmental_needs_doctypes.py` to the new schema set | Done | 7 schemas, native `BUSINESS_PERMISSIONS` replacing `CONTROLLED_PERMISSIONS = []` |
| NDS-110 | Focused tests: field validation, root/version pointers, immutability | Done | New `tests/test_departmental_needs_domain_model.py` — **25 tests, 25 passed** (`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.test_departmental_needs_domain_model`, 0.966s) |
| NDS-111 | **Added in Phase 1** — create the governed unit catalogue (`Unit Of Measure`) in `kentender_core` | Done | §3 assigns the unit catalogue to Configuration & Governance and §4.3 requires `unit_id` to be a governed Link, but no such doctype existed anywhere in the repo (the only `uom` hits were the legacy `Demand Item` model and archived code). Created `kentender_core/.../doctype/unit_of_measure/` with `UNIT-PROGRAMME` and `UNIT-EACH` seeded per §14.1. Test `test_unit_links_to_the_governed_catalogue` |
| NDS-112 | **Added in Phase 1** — native permissions brought forward from Phase 3 | Done | Unavoidable: the slimmed root removed `status`/`submitted_by`/`target_financial_year`, the exact fields `services/permissions.py` read. Rewritten against Frappe roles + User Permission (`permitted_values`/`in_scope`), all `CAP_*` identifiers deleted from `constants.py`. Phase 3 now only owns the remaining scope-behaviour tests and the page-role cleanup |
| NDS-113 | **Added in Phase 1** — seed rebuilt onto the version model | Done | `seeds/kentender_mvp_r1.py` rewritten: native roles + User Permission (no Capability Profile), §14.3's four Needs with exact descriptions/expected operational results, acting-HoD scoped to Digital Health only. Ran twice → identical result (`{"needs": [...0001..0004]}`), counts stable at 4 Needs / 5 Versions / 3 Decisions / 2 Units. Full §14 (usage, successor, withdrawal, KEBS profiles) remains Phase 6 |

## Work register — Phase 2: services and lifecycle

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-201 | Rewrite `lifecycle.py` §5.1 initial lifecycle; return creates a copied correction Draft | Done | Landed in Phase 1; Phase 2 added the NDS-BR-002/003 intake gate (initial create + initial submit gated; a returned correction resubmits after close) and moved every action label onto `ACTION_*` constants. Tests `test_create_generates_reference_and_draft_version_one`, `test_return_preserves_the_submitted_version_and_copies_a_correction_draft`, `test_a_returned_correction_may_be_resubmitted_after_the_window_closes` |
| NDS-202 | Implement §5.2 successor lifecycle (`create_accepted_need_successor`, `cancel_accepted_need_successor`, accept/return/decline of a successor) | Done | Both commands added; `update_need`/`submit_need`/`review_need` are now successor-aware, branching on `_open_successor()` and the task type. **The root stays `Accepted for planning` for the whole successor lifecycle** — the only reading consistent with §5.2's "earlier accepted version remains effective"; the successor's own `version_status` carries its state. Accept supersedes atomically in one transaction (NDS-AC-017); decline and cancel repoint `current_version` back to the accepted version (NDS-AC-018, NDS-AC-033). 8 tests in `TestAcceptedSuccessorLifecycle` |
| NDS-203 | Implement §5.3 withdrawal decisions incl. `Evaluate`, re-evaluate and `Decline` | Done | `approve_withdrawal` replaced by `decide_withdrawal(decision=approve\|evaluate\|decline)`. `Evaluate`/`Re-evaluate` rotate the decision token but leave the task **Open** (the request is not resolved); only approve and decline close it. `planning_dependency_version` (§4.6) is now written on every decision. **Corrected the dependency predicate**: the previous code blocked on Draft *or* Effective allocations, but §5.3 states plainly that a Draft or Submitted DPP is not an Active Plan dependency — the block is now Effective-only and scoped to the exact accepted version (NDS-BR-016). 9 tests in `TestAcceptedWithdrawalLifecycle` |
| NDS-204 | Correct `_validate_submission()` to §4.3 bounds; delete validation for removed fields | Done | Landed in Phase 1 (10–1,000 each for description and expected operational result, positive quantity, active governed unit, in-year required-by) |
| NDS-205 | Delete `services/attachments.py` | Done | Deleted in Phase 1 |
| NDS-206 | Rewrite `services/context.py` against the real intake window, inclusive boundaries | Done | `intake_window()` derives `Scheduled`/`Open`/`Closed` from the stored instants at read time with **both boundaries inclusive**; `require_open_intake()` raises the §9 `NDS_INTAKE_NOT_OPEN`. `save_intake_window()` (§8.2) added, Planner-scoped with an optimistic-lock check. Verified live at the exact `opens_at` and `closes_at` instants. Two invented error codes (`NDS_INTAKE_WINDOW_NOT_CONFIGURED`, `NDS_FINANCIAL_YEAR_CLOSED`) replaced with the §9 `NDS_CONTEXT_REQUIRED`. Test `test_state_is_derived_with_inclusive_boundaries` |
| NDS-207 | Reduce `services/usage.py` to `Not included` / `Fully included` | Done | Landed in Phase 1 |
| NDS-208 | Extend `services/notifications.py` to withdrawal decisions | Done | Landed in Phase 1; Phase 2 wired the request/approve/decline events to actual command call sites |
| NDS-209 | Rewrite `services/workspace.py` projections to the §11.2/§11.3 shape (one table, no summary cards) | Done | Landed in Phase 1; Phase 2 repointed its FY list at the governed `Financial Year` catalogue (see NDS-212) |
| NDS-210 | Focused tests: every §5 transition, idempotency, concurrency, maker-checker | Done | New `tests/test_departmental_needs_lifecycle.py` — **39 tests, 39 passed**, 5.9s |
| NDS-211 | **Added in Phase 2** — seed the §14.1 Needs intake window | Done | The NDS-BR-002 gate is meaningless without a window record, so the §14.1 window (1 Sep 2026 00:00:00 → 25 Nov 2026 23:59:59) is now seeded for `PE-MOH`/`FY-2027-2028`. **Consequence to note:** at real wall-clock dates before 1 Sep 2026 that window is correctly `Scheduled`, so manual Need creation returns `NDS_INTAKE_NOT_OPEN` until then. Tests set their own instants inside their own transaction rather than moving the fixture |
| NDS-212 | **Added in Phase 2** — the FY validation resolved against the wrong doctype | Done | **Pre-existing defect, found by the first test to exercise the path.** `selectable_financial_year()` resolved through `kentender_core.services.financial_context`, which operates on ERPNext's `Fiscal Year` (identifiers like `2027/28`), while this module's Link field, its `Financial Year` User Permission dimension and `_next_reference()` all use the governed `Financial Year` catalogue (`FY-2027-2028`). Every call therefore threw `KT_FY_NOT_ENABLED` — meaning `create_need` and the `_validate_submission` required-by check could never have succeeded for a seeded Need. Now resolved against `Financial Year`, requiring `record_status = Available` and rejecting only expired years |
| NDS-213 | **Added in Phase 2** — a future target financial year must be permitted | Done | The old guard rejected `is_future` years. §14.1 collects **FY 2027/28** Needs in a **Sep–Nov 2026** window, so a future target year is the normal case, not an error; what governs timing is the intake window (NDS-BR-002), not whether the target year has started. `selectable_financial_year` and the workspace/context FY lists now reject only expired years. Test `test_create_is_allowed_for_a_future_target_financial_year` |

## Work register — Phase 3: permissions

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-301 | Replace `authorization_policy` usage with native Frappe permissions; populate the DocType permissions array | Planned | |
| NDS-302 | Scope PE/FY/department through User Permission | Planned | |
| NDS-303 | Acting HoD = same role + time-bound scoped User Permission; delete `Departmental Review Delegate` and the delegation path in `notifications.py` | Planned | |
| NDS-304 | Remove Budget Officer / Accounting Officer / Planner landing page from `setup/departmental_needs_page.py` | Planned | |
| NDS-305 | Planner gets intake-window maintenance + read-only accepted-source link only | Planned | |
| NDS-306 | Delete the support-lookup surface (`workspace.py::get_support_need`) | Planned | |
| NDS-307 | Permission tests: own vs department vs acting-HoD vs Planner vs auditor; cross-OU/PE/FY denial | Planned | |

## Work register — Phase 4: API and command surface

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-401 | Rewrite `api.py` to the §8.1 read contracts | Planned | |
| NDS-402 | Rewrite `api.py` to the §8.2 commands with idempotency key + expected token | Planned | |
| NDS-403 | Implement the full §9 error contract as stable codes | Planned | |
| NDS-404 | Confirm no writable DocType endpoint bypasses a command (§16.1) | Planned | |

## Work register — Phase 5: Planning integration

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-501 | Emit `DepartmentalNeedAccepted.v2` with exactly the §7.1 field list | Planned | |
| NDS-502 | Add `DepartmentalNeedSuperseded.v1` and `DepartmentalNeedWithdrawn.v1`; outbox delivery, idempotent, ordered per Need | Planned | |
| NDS-503 | Consume `NeedPlanningUsageChanged.v1`; stop querying `Plan Need Allocation` | Planned | Cross-module — sequence with PLN-CHG-001 v1.1 |
| NDS-504 | Repo-wide grep for real consumers of the old payload before changing it | Planned | |
| NDS-505 | Contract tests for all three events + stale-hash handling | Planned | |

## Work register — Phase 6: seeds and fixtures

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-601 | §14.1 prerequisites + §14.2 seven actors | Planned | |
| NDS-602 | §14.3 four Needs with exact descriptions and expected operational results | Planned | |
| NDS-603 | §14.4 Planning-usage profile; §14.5 successor and withdrawal profiles (independently selectable) | Planned | |
| NDS-604 | §14.6 KEBS first-slice profile | Planned | |
| NDS-605 | Idempotency proof: seed twice, identical result | Planned | |

## Work register — Phase 7: frontend

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-701 | NDS-UI-01 workspace (DES-01) + five states (DES-14a–e) | Planned | |
| NDS-702 | NDS-UI-02 department review, both tabs (DES-02, 02b) | Planned | |
| NDS-703 | NDS-UI-03 editor (DES-03, 04, 08) — six fields, help text, no items/attachments/cost/location | Planned | |
| NDS-704 | NDS-UI-04 detail (DES-05, 07) + Create update / Request withdrawal / View Plan Item | Planned | |
| NDS-705 | NDS-UI-05 review task (DES-06, 09) + dialogs DES-13a/13b | Planned | |
| NDS-706 | NDS-UI-06 accepted source detail | Planned | |
| NDS-707 | NDS-UI-07 withdrawal review (DES-12a/12b) + request dialog DES-11 | Planned | |
| NDS-708 | NDS-UI-08 intake window (DES-10) | Planned | |
| NDS-709 | Delete legacy jQuery pages, JS and CSS | Planned | |
| NDS-710 | Stable accessible test selectors; unmount/cancel on route change (active-flag guard, not `router.off()`) | Planned | |

## Work register — Phase 8: shell and registry wiring

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-801 | Register the 8 canonical routes in `kt_cl_surface_registry.js` | Planned | |
| NDS-802 | Module menu: 3 entries with correct role visibility; placed after Budget & Funding | Planned | |
| NDS-803 | `hooks.py` updated; old Page records removed | Planned | |
| NDS-804 | Clean whole-site `bench migrate` (watch the workspace-sidebar reverse-sync hazard) | Planned | |

## Work register — Phase 9: tests

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-901 | Static-scan test: no prohibited field, object, role or legacy route | Planned | Extends the `test_departmental_needs_completeness_gaps.py` boundary-test pattern |
| NDS-910 | **Architecture test enforcing the D1 module boundary**: `procurement_planning` must not import a `departmental_needs` DocType, query a `tabDepartmental Need*` table, or call a `departmental_needs.services.*` internal — the published handoff contract is the only permitted path. Assert in both directions (Needs must not reach into Planning internals either). | Planned | Required by the Project Owner's firm D1 decision; failing this test fails the phase |
| NDS-902 | Domain unit layer (§15.1) | Planned | |
| NDS-903 | Permission unit layer | Planned | |
| NDS-904 | Command integration layer | Planned | |
| NDS-905 | Contract integration layer | Planned | |
| NDS-906 | UI component layer | Planned | |
| NDS-907 | Playwright browser smoke for all 8 screens | Planned | |
| NDS-908 | Visual regression at 1440 × 1024 for every artboard, modal and workspace state | Planned | |
| NDS-909 | Delete `test_departmental_needs_attachments.py` and the delegate-review case | Planned | |

## Work register — Phase 10: verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| NDS-1001 | Complete the AC mapping table below with per-criterion evidence | Planned | |
| NDS-1002 | §19 E2E-REQ-001 conformance check — all 8 non-drift controls | Planned | |
| NDS-1003 | Live browser walkthrough: golden path + edge cases; first paint **and** interactive re-render | Planned | |
| NDS-1004 | Zero page console errors, zero failed own requests | Planned | |
| NDS-1005 | Production-mode asset build; §16.3 release evidence assembled | Planned | |

## Acceptance-criteria mapping (§15)

All 45 criteria. Evidence is filled in as phases complete; `Planned` means no evidence yet.

| AC | Criterion (abbrev.) | Phase | Status | Evidence |
|---|---|---|---|---|
| NDS-AC-001 | Six values only; no item table, no funding field | 1 | Planned | |
| NDS-AC-002 | Explicit server-authorised context; no fallbacks | 3 | Planned | |
| NDS-AC-003 | Create/submit only inside the intake window, inclusive boundaries | 2 | Done | `test_state_is_derived_with_inclusive_boundaries` (both boundary instants Open), `test_create_outside_the_intake_window_is_refused`, `test_initial_submission_outside_the_window_is_refused`, `test_a_returned_correction_may_be_resubmitted_after_the_window_closes` (NDS-BR-003) |
| NDS-AC-004 | Partial Draft saves after title; submission rejects missing values | 2 | Partial | `test_save_draft_updates_the_current_version` and Phase 1's `_content_values` allow a title-only Draft. The **per-field rejection paths** on submit are still owed as focused tests (DEBT-02, NDS-902) |
| NDS-AC-005 | Required-by inside FY; quantity positive | 2 | Planned | |
| NDS-AC-006 | Unit from active governed catalogue; no free-text `Other` | 1 | Planned | |
| NDS-AC-007 | No Budget Line/amount/funding source/currency anywhere | 1 | Planned | |
| NDS-AC-008 | No reservation or availability check | 2 | Planned | |
| NDS-AC-009 | Submit = one version/hash + one task + one notification, atomic and idempotent | 2 | Partial | `test_submit_locks_the_version_hashes_it_and_opens_one_task` asserts the immutable hash and **exactly one** open task; idempotency asserted by `test_replaying_an_idempotency_key_creates_no_second_decision`. The **notification-effect** assertion is still owed (DEBT-02, NDS-906) |
| NDS-AC-010 | Maker cannot decide; expired/cross-scope fails closed | 2, 3 | Partial | Maker-checker done in Phase 2: `test_the_maker_of_a_version_cannot_decide_it` (an HoD who authored the Need is still refused) and `test_an_author_without_review_authority_is_denied_before_maker_checker`. **Expired and cross-scope** review assignments remain Phase 3 |
| NDS-AC-011 | Return requires reason, preserves version, creates one copied Draft | 2 | Done | `test_return_preserves_the_submitted_version_and_copies_a_correction_draft`, `test_return_without_a_reason_is_refused`; successor variant `test_returning_a_successor_copies_a_correction_and_keeps_the_accepted_version` |
| NDS-AC-012 | Decline requires reason; Accept collects none | 2 | Done | `test_decline_requires_a_reason_and_closes_the_need`, `test_accept_sets_the_accepted_pointer_and_collects_no_reason` (asserts the Decision row's reason is empty). Reason requirement is driven by `REASON_REQUIRED_ACTIONS`, not per-branch conditionals |
| NDS-AC-013 | Accept creates no Plan Item/objective/classification/Requisition/Tender | 2 | Planned | |
| NDS-AC-014 | Planning uses current accepted version at full quantity; no partial | 5 | Planned | |
| NDS-AC-015 | Usage independent of lifecycle; only Not/Fully included | 2, 5 | Planned | |
| NDS-AC-016 | Accepted version immutable; open successor does not replace it | 2 | Done | `test_create_update_copies_the_accepted_version_and_leaves_it_effective`, `test_saving_an_update_edits_only_the_successor` (asserts the accepted version's required-by is unchanged). Reinforced by the version controller's `_guard_immutable_content` from Phase 1 |
| NDS-AC-017 | Successor acceptance supersedes atomically with lineage | 2, 5 | Partial | `test_accepting_a_successor_atomically_supersedes_the_earlier_version` — supersession, repointing and the decision record all happen in one transaction, and `based_on_version` carries the lineage. The **published event** half is Phase 5 |
| NDS-AC-018 | Successor decline leaves earlier accepted version current | 2 | Done | `test_declining_a_successor_leaves_the_earlier_version_current` |
| NDS-AC-019 | Accepted withdrawal maker-checked; blocked by Active Plan dependency | 2 | Done | `test_the_requester_cannot_decide_their_own_request`, `test_approve_is_blocked_while_an_active_plan_dependency_exists`, `test_evaluate_moves_the_request_to_awaiting_planning_clearance`, `test_re_evaluating_while_still_included_changes_no_state`, `test_approve_succeeds_once_planning_clears_the_inclusion`, `test_a_draft_plan_allocation_is_not_an_active_plan_dependency`. The dependency is re-read inside the deciding transaction, so approve cannot complete on a stale clear |
| NDS-AC-020 | Planning clearance only in Planning; no foreign-module mutation | 5 | Planned | |
| NDS-AC-021 | One scope predicate for search/counts/rows/detail/export/services | 3 | Planned | |
| NDS-AC-022 | Role permissions match §6 exactly | 3 | Planned | |
| NDS-AC-023 | Budget Officer / Accounting Officer get nothing | 3 | Planned | |
| NDS-AC-024 | Payload includes expected result; excludes the named 9 concepts | 5 | Planned | |
| NDS-AC-025 | DES-01–14 render exact fixtures and exclusions | 7, 9 | Planned | |
| NDS-AC-026 | Breadcrumb/header outside artboards; framework components used | 7 | Planned | |
| NDS-AC-027 | Runtime behaviour from §12, not inferred from design output | 7 | Planned | |
| NDS-AC-028 | Stale/duplicate/concurrent commands create no duplicates | 2 | Done | `test_a_stale_record_version_overwrites_nothing` (asserts the value was not written), `test_a_stale_decision_token_is_refused`, `test_replaying_an_idempotency_key_creates_no_second_decision` (asserts exactly one Decision row) |
| NDS-AC-029 | No location/attachment/source ref/notes/contact/Strategy/classification/line-item field | 1, 9 | Planned | |
| NDS-AC-030 | No `/demands`, `/departmental-needs`, `/desk/departmental-needs` compatibility route | 8, 9 | Planned | |
| NDS-AC-031 | Planning shell/Plan Item UI reused; Planning adds direct-requirement editor | 5 | Planned | Cross-module (PLN-CHG-001 v1.1) |
| NDS-AC-032 | Fresh environment builds clean schema + selectable seed profiles | 6 | Planned | |
| NDS-AC-033 | Cancelling a Draft successor withdraws only that successor | 2 | Done | `test_cancelling_an_update_withdraws_only_the_successor` |
| NDS-AC-034 | HoD/preparer can create a direct requirement without a Need | 5 | Planned | Cross-module |
| NDS-AC-035 | DPP may be all-direct, all-Need, or mixed | 5 | Planned | Cross-module |
| NDS-AC-036 | Direct requirement creates no synthetic Need/task/reason/audit event | 5 | Planned | Cross-module |
| NDS-AC-037 | Need-origin entries keep Need/version/hash lineage; direct entries keep DPP lineage | 5 | Planned | Cross-module |
| NDS-AC-038 | Expected operational result in accepted version and `DepartmentalNeedAccepted.v2` | 1, 5 | Planned | |
| NDS-AC-039 | Need ID stays the stable source-line identity through Planning | 5 | Planned | |
| NDS-AC-040 | Planning receives expected result read-only; no supplier obligation or Tender parameter | 5 | Planned | |
| NDS-AC-041 | Only Departmental Author and HoD perform lifecycle actions | 3 | Planned | |
| NDS-AC-042 | Acting HoD via same role + time-bound User Permission; no delegate role | 3 | Planned | |
| NDS-AC-043 | Planner maintains intake window, receives no Need decision | 3, 7 | Planned | |
| NDS-AC-044 | Native Frappe permissions enforce scope; no parallel permission system | 3 | Planned | |
| NDS-AC-045 | KEBS Needs-origin and direct-Planning profiles preserve equivalent source facts | 6 | Planned | |

## §19 E2E-REQ-001 conformance check

| Non-drift control | Phase | Status | Evidence |
|---|---|---|---|
| Structured data is authoritative; no attachment substitute | 1 | Planned | |
| Fixed product forms — exactly six user-owned values | 1 | Planned | |
| No generic configuration engine | 9 | Planned | |
| Enter department data once — same Need/version IDs pass to Planning | 5 | Planned | |
| Procurement cannot silently rewrite — Planning receives values read-only | 5 | Planned | |
| Downstream obligations linked via the stable source ID | 5 | Planned | |
| Native Frappe permissions and minimum roles | 3 | Planned | |
| No premature abstraction — no generic requirement model | 9 | Planned | |
