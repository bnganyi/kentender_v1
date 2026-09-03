# STR-CHG-001 v1.6 — Strategy Alignment rebuild — tracker

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_6.md` (approved 3 September 2026).
**Companions:** `02_STR_Rebuild_Gap_Analysis.md`, `03_STR_Rebuild_Implementation_Plan.md`, `FOLLOW_UPS.md`.
**Status:** **Phase 0 complete.** Phases 1–9 not started.
**Started:** 2026-09-03

## Tracker rules

1. Rows are permanent and use `Planned`, `In progress`, `Blocked`, `Done`.
2. `Done` requires the row's own evidence (a command, a test name, a diff, a described screenshot) — not "looks right."
3. If a touched file still references a concept §1.1 or §17 prohibits (`procuring_entity_id`, `pe_fy_context`, `owner_org_unit_id`, `financial_year_id` as a fieldname, `Strategy Viewer`, `Strategy Reviewer`, `Strategy Approval Authority`, a retired lifecycle status, `STRATEGY_SCOPE_REQUIRED`, `STRATEGY_PERMISSION_DENIED`, or any disposed concept from §1.1's register), the row that touches it is not `Done`.
4. No row may introduce an alias, redirect, dual-write, compatibility shim, or parallel legacy+new surface. If one appears, treat it as a defect in that row, not a valid completion.
5. §11 (Claude Design contract) governs visual/content fidelity only. §1–10 and §12–19 govern behaviour. A row implementing behaviour from §11 content instead of §12 is a defect, not a shortcut.
6. Deletion lands in the same phase as its replacement. "Delete later" is not a valid row state.
7. A row claiming CU-3xx (commit `ccff1b80`) already covers an item must cite the specific file:line evidence, not just the commit hash — this tracker's Phase 1 exists precisely to re-verify those claims once, not to take them on faith indefinitely.

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-09-03 | Treat this as a **correction pass**, not a rebuild from scratch. | Commit `ccff1b80` (CU-3xx), landed the same day v1.6 was approved, already migrated Strategy's authorization onto the site-wide URA model, stripped most PE parameters from services, deleted the leftover "Strategy Manager" role, and updated 64 tests. `02_STR_Rebuild_Gap_Analysis.md` §2 catalogues what's already done; the remaining gaps are specific and bounded, not a full domain-model rebuild. |
| 2026-09-03 | **D1 — `kentender_scope_map` registration.** Keep CU-302's decision not to register Strategy DocTypes into the map, despite §16.1's literal instruction to do so. Documented as a deviation, flagged to the AUTH-ADR-001 owner as a possible spec erratum. | §16.1 says register because "the registered predicate reduces to an assignment existence check" for a site-wide role — but no OU field survives on `Strategic Plan` after Phase 2 to name in a map entry, and the ADR's own documented map shape (`{"DocType": {"ou_field": ...}}`) doesn't match the real merge code in `kentender_core.services.authorization` (flat string values only). Writing an entry that mechanically satisfies §16.1's text while referencing a field being deleted in the same pass would be self-contradictory. DocPerm-via-URA-projection is the correct, already-working list gate for a site-wide role. |
| 2026-09-03 | **D2 — `StrategyAuditEvent` (§4.6).** Keep the shared `kentender_core.audit_event_service`; no dedicated Strategy doctype. Close the one real gap (exercised responsibility assignment ID) by threading `decision.assignment.name` through instead of a capability label string. | A prior decision (`strategy_audit.py:1-9`) already rejected a bespoke doctype as duplicate mechanism, and an existing test (`test_str_chg_001_phase1_domain_model.py`) asserts its absence. Every other §4.6 field is already correctly threaded through the shared service. Building a new doctype now would reverse a settled decision to fix one field. |
| 2026-09-03 | **D3 — dead two-PE seed text.** Delete the ~120 lines of unreachable `PE-MOH`/`PE-CGKIS` dataset definitions in `kentender_mvp_v1_strategy.py` entirely, not just leave the CU-307 stub in place. Rebuild the orphaned STR-DES v2 artboard-fixture generator off the live single-PE seed identity. | §1's "deleted rather than aliased, redirected, dual-read or retained behind feature flags" reads naturally as covering the file's text, not only its reachable execution path. The dead code is also a live trap — an orphaned function (`seed_str_des_v2_fixture`) that would throw obscurely if ever called, rather than failing loudly and clearly. §14.4 still needs the Version-2 fixture mechanism, so this is a rebuild of that one piece, not a bare deletion. |
| 2026-09-03 | **D4 — doc naming/structure.** Mirror NDS/Planning's convention exactly: restart Strategy's own doc numbering at `02_`/`03_`; add a standalone gap-analysis doc (Strategy's prior generation skipped this doc type); use a separate `FOLLOW_UPS.md`. | Per-repo convention is to mirror the most recent, structurally consistent sibling precedent for full-replacement change docs. NDS and Planning are that precedent; Budget's own plan/tracker docs were deleted historically and are a weaker template. Strategy's own immediate predecessor folded follow-ups into its tracker instead — noted as a deliberate deviation from that specific precedent, in favour of the more current one. |
| 2026-09-03 | **D5 — UI route architecture (§10).** Explicitly deferred, not resolved. Phase 1 must produce a live route trace before Phase 6 is sized. | Whether the current three-Page Desk split satisfies §10's literal path-segment routes, or requires Departmental-Needs-style single-Page consolidation, is not decidable from spec text or static code reading alone — it depends on actual runtime behaviour (direct load, refresh, back/forward) that hasn't been observed yet. Guessing here risks sizing Phase 6 wrong in either direction. |

## Headline findings (read before touching code)

1. **This module is mid-cutover, not pre-cutover.** Commit `ccff1b80` landed the same day as v1.6's approval and already did the hard authorization-model work. Re-verify what it claims (Phase 1); do not re-plan it.
2. **Two schema fields are hidden but not gone.** `procuring_entity_id`/`pe_fy_context` on `Strategic Plan` carry `hidden=1, read_only=1` and an explicit "Column retained until the removal phase" description — a clear marker that a future phase (this one) was always expected to finish the job.
3. **`owner_org_unit_id` is not just a field to drop — it's live business logic.** `_assert_no_primary_overlap()` reads it to partition STR-BR-004's overlap check. Deleting the column without rewriting the predicate either crashes or silently changes what counts as a conflicting plan.
4. **`resolve_strategy_context()` leaks scope data it shouldn't return.** Confirmed by direct read (`strategy_consumer.py:112-115`): the payload includes `"procuring_entity"` and `"organisation_unit"` keys, and the API wrapper still accepts a `procuring_entity` kwarg it silently drops as a "transport-compat bridge."
5. **`strategy_contracts.py` is ~1,450 lines of dead code**, only 4 of its ~30 functions ever imported. It still references three deleted doctypes by name — a real STR-AC-002 violation despite being unreachable.
6. **The route-architecture question is genuinely open**, not a rubber-stamp. Both "current three-Page split is fine" and "needs single-Page consolidation" are plausible outcomes; Phase 1 must observe live behaviour before Phase 6 can be sized.
7. No Strategy design-fidelity gate exists yet. The new artboard set on disk (dated today) has not been verified against §11 by any automated check.

## Carried debts

None yet — no implementation phase has executed. This section is populated as phases close, per the NDS/Planning tracker convention: a debt is recorded here the phase it is opened, and closed (struck through, not deleted) in the phase that resolves it.

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| STR-G00 | Gap analysis, plan and tracker authored | Done | `02_STR_Rebuild_Gap_Analysis.md`, `03_STR_Rebuild_Implementation_Plan.md`, this document. D1-D4 resolved with the module owner; D5 recorded as explicitly deferred |
| STR-G01 | Repo-wide static scan complete; route-architecture question resolved (D5) | Planned | — |
| STR-G02 | Schema matches §4.1/§4.5 exactly; STR-BR-004 rewritten and DB-guarded; clean `bench migrate` | Planned | — |
| STR-G03 | `resolve_strategy_context()` matches §7/§8 literally; cross-app gateway contract test green | Planned | — |
| STR-G04 | `Strategy Viewer` role fully removed; D1 recorded as a documented non-action | Planned | — |
| STR-G05 | `strategy_contracts.py` deleted; dead seed code removed; D2 assignment-ID gap closed | Planned | — |
| STR-G06 | UI route architecture corrected per Phase 1's D5 finding (or confirmed no-op with owner sign-off) | Planned | — |
| STR-G07 | New artboard set verified against §11; `make ui-strategy-fidelity-gate` passes | Planned | — |
| STR-G08 | §14 seed contract satisfied; KT-STD-001 §8.3/§8.5 updated; idempotent on rerun | Planned | — |
| STR-G09 | All 34 STR-AC IDs evidenced; full module + cross-app + AUTH contract suites green; static scan clean | Planned | — |

## Work register — Phase 0: gap analysis, plan and tracker

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-001 | Read STR-CHG-001 v1.6 in full; identify the §1.1 disposition register and §16.1 implementation rules as the primary gap surface | Done | `02_STR_Rebuild_Gap_Analysis.md` §3, §10 |
| STR-002 | Baseline the current `kentender_strategy` implementation (doctypes, services, api, roles, UI, seeds, tests) against the spec, including what commit `ccff1b80` already changed today | Done | `02_STR_Rebuild_Gap_Analysis.md` §2, §4–9; direct reads of `strategic_plan.json` and `strategy_consumer.py` confirmed the Plan-agent's findings |
| STR-003 | Verify the AUTH-ADR-001/KT-STD-001/CFG-CHG-002 mechanisms Strategy depends on actually exist and behave as documented (business-role registry, `authorise_record()`, `kentender_scope_map` shape, `GetSiteConfiguration()`) | Done | Explore-agent pass verified `business_role_registry.py`, `authorization.py`, `site_configuration.py` against the ADR/STD/CFG doc text; found the `kentender_scope_map` doc/code shape mismatch (informs D1) |
| STR-004 | Survey sibling rebuild docs (NDS, Planning) for naming/structure precedent | Done | NDS's `02_.../03_.../IMPLEMENTATION_TRACKER.md/FOLLOW_UPS.md` convention adopted (D4) |
| STR-005 | Resolve D1-D4 with the module owner; record D5 as explicitly deferred to Phase 1 | Done | See Decision log above |
| STR-006 | Author `02_STR_Rebuild_Gap_Analysis.md`, `03_STR_Rebuild_Implementation_Plan.md`, this tracker, `FOLLOW_UPS.md` | Done | This document and its three companions |

## Work register — Phase 1: repo-wide static verification and route-architecture research

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-101 | Repository-wide disposed-concept grep across `kentender_strategy`, `kentender_procurement`, `kentender_budget`, `kentender_core` | Planned | — |
| STR-102 | Confirm or refute the STR-BR-004 database-level partial unique index (§16.1) | Planned | — |
| STR-103 | Confirm whether `Auditor` is a registered business-role-registry entry or a bare Strategy DocPerm role | Planned | — |
| STR-104 | Live route trace: direct load / refresh / back-forward behaviour of `/app/strategy-portfolio` and `/app/strategy-plan-workspace/<id>` against §10's literal route table | Planned | — |
| STR-105 | Decide (with module owner) whether the three-Page split is acceptable or single-Page consolidation is required (D5) | Planned | Blocks Phase 6 sizing |

## Work register — Phase 2: schema correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-201 | Drop `procuring_entity_id` and `pe_fy_context` from `Strategic Plan` | Planned | — |
| STR-202 | Drop `owner_org_unit_id` from `Strategic Plan` | Planned | — |
| STR-203 | Rename `financial_year_id` → `fiscal_year` on `Performance Target` | Planned | — |
| STR-204 | Rewrite `_assert_no_primary_overlap()` to drop OU-partitioned logic; enforce STR-BR-004 with no PE/OU qualifier | Planned | — |
| STR-205 | Build the DB-level partial unique index guard if STR-102 confirms it's missing | Planned | — |
| STR-206 | New migration patch for the field drops + rename | Planned | — |

## Work register — Phase 3: service and command contract correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-301 | Rebuild `resolve_strategy_context()` to the literal §7/§8 shape (drop `organisation_unit` param + OU filter; add `fiscal_year` input + `include_supporting`; strip `procuring_entity`/`organisation_unit` from the payload) | Planned | — |
| STR-302 | Update `api/strategy_consumer_api.py` wrapper; drop the `procuring_entity` transport-compat kwarg | Planned | — |
| STR-303 | Verify `strategy_gateway.py` + `test_gateway_contracts.py` against the corrected signature | Planned | — |

## Work register — Phase 4: roles and permission cleanup

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-401 | Remove `Strategy Viewer` DocPerm rows from all 5 doctype JSONs + Page/Workspace JSONs | Planned | — |
| STR-402 | Remove `ROLE_VIEWER`/`UNRESTRICTED_READ_ROLES` references in `strategy_permissions.py`/`strategy_ui_contracts.py` | Planned | — |
| STR-403 | New patch hard-deleting the `Strategy Viewer` Role | Planned | — |
| STR-404 | Confirm and clean any remaining `Strategy Viewer` seed pairing in `kentender_core` | Planned | — |
| STR-405 | Record D1 (`kentender_scope_map` non-registration) as a documented non-action | Planned | — |

## Work register — Phase 5: dead code removal

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-501 | Extract 4 live-used functions out of `strategy_contracts.py` into `strategy_consumer.py` | Planned | — |
| STR-502 | Delete `strategy_contracts.py` wholesale; update the 2 dependent test files | Planned | — |
| STR-503 | Delete dead two-PE dataset text in `kentender_mvp_v1_strategy.py` (D3) | Planned | — |
| STR-504 | Rebuild `seed_str_des_v2_fixture()`/`teardown_str_des_v2_fixture()` off the live single-PE seed identity | Planned | — |
| STR-505 | Thread `decision.assignment.name` into `strategy_audit.py::record_event()` metadata (D2) | Planned | — |
| STR-506 | Fix stale `v1.5 §7` citation at `business_role_registry.py:177-178` | Planned | — |

## Work register — Phase 6: UI route architecture correction

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-601 | Execute the D5 outcome from STR-105 (consolidation, or no-op with recorded sign-off) | Planned | Scope depends entirely on Phase 1 |
| STR-602 | Browser journey proving direct-load/refresh/back-forward for all 4 canonical routes | Planned | — |

## Work register — Phase 7: artboard / design-fidelity verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-701 | Verify new STR-DES-01..10/Shell/index artboards against §11 exact content | Planned | — |
| STR-702 | Resolve the CU-3xx "9 of 20 artboards depict PE dimension" note against the *new* artboard set | Planned | — |
| STR-703 | Build `strategy-fidelity.spec.ts` + `make ui-strategy-fidelity-gate`, cloning the System Setup pattern | Planned | — |
| STR-704 | Audit the 3 legacy `ui-strategy-*-gate` Makefile targets for staleness | Planned | — |

## Work register — Phase 8: seed contract alignment

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-801 | Add 3 Strategy actors + fixture timeline to KT-STD-001 §8.3/§8.5 | Planned | — |
| STR-802 | Verify/build the exact §14.3 MOH plan seed | Planned | — |
| STR-803 | Verify §14.2 fail-closed FY-2027-2028 check against ERPNext `Fiscal Year` | Planned | — |
| STR-804 | Verify rebuilt V2 fixture matches §14.4 exactly | Planned | — |

## Work register — Phase 9: acceptance-contract mapping and release verification

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| STR-901 | Map all 34 STR-AC IDs to tests/evidence (table below) | Planned | — |
| STR-902 | Full `kentender_strategy` suite green | Planned | — |
| STR-903 | Cross-app contract suite (Budget + Procurement) green | Planned | — |
| STR-904 | AUTH contract suite green — no Strategy path reintroduces a User Permission read | Planned | — |
| STR-905 | Re-run Phase 1's static scan; confirm clean | Planned | — |

## Acceptance-criteria mapping (§15)

Every row starts `Planned`, closed with cited evidence as phases complete.

| ID | Criterion (condensed) | Phase(s) | Status | Evidence / gap |
|---|---|---|---|---|
| STR-AC-001 | Module installs/imports without legacy Demands package or Procurement Home | 1, 9 | Planned | — |
| STR-AC-002 | No executable metadata/route/service/field/label/seed/test refers to disposed concepts | 5, 9 | Planned | Primary target: `strategy_contracts.py` dead code |
| STR-AC-003 | Strategy Author creates a Draft plan, receives generated references | — | Planned | Likely already satisfied by CU-3xx; confirm in Phase 1 |
| STR-AC-004 | No Active assignment (incl. Administrator/System Manager) cannot create/submit/return/approve | — | Planned | Likely already satisfied by CU-3xx; confirm in Phase 1 |
| STR-AC-005 | Draft hierarchy Pillar→Programme→optional Sub-programme→Objective, Indicator/Target nesting | — | Planned | No known gap |
| STR-AC-006 | Strategic Objective and Performance Indicator distinct; no Strategic Outcome | 5 | Planned | Confirmed absent as doctype; dead-code references remain |
| STR-AC-007 | Target validation: period, comparison, unit-compatible value, percentage range | — | Planned | No known gap |
| STR-AC-008 | Readiness blocks submission on invalid identity/hierarchy/missing content | — | Planned | No known gap |
| STR-AC-009 | Plan Item selects exactly one Objective, not Indicator/Target | — | Planned | No known gap (Procurement-Planning-owned UI, Strategy contract side only) |
| STR-AC-010 | Only Strategy Author/Approver are workflow responsibilities; no self-approval | — | Planned | Likely already satisfied by CU-3xx; confirm in Phase 1 |
| STR-AC-011 | Return requires reason; preserves full workflow history | — | Planned | No known gap |
| STR-AC-012 | Submitted/Active/Superseded immutable; correction via successor version | — | Planned | No known gap |
| STR-AC-013 | Concurrent approval cannot create overlap, even bypassing the command layer | 2 | Planned | Blocked on STR-204/STR-205 (DB-level guard) |
| STR-AC-014 | Successor approval atomically activates + supersedes | — | Planned | No known gap |
| STR-AC-015 | Zero/multiple context matches return typed errors, never chosen by preference | 3 | Planned | Confirm against rebuilt `resolve_strategy_context()` |
| STR-AC-016 | `resolve_strategy_context` returns correct version, requires no PE/OU input | 3 | Planned | Direct gap — payload currently leaks PE/OU (STR-301) |
| STR-AC-017 | `list_strategy_objectives` returns only Active Objectives with IDs + ancestor paths | — | Planned | No known gap |
| STR-AC-018 | `get_strategy_lineage` returns exact IDs/types/titles in order | — | Planned | No known gap |
| STR-AC-019 | `create_strategy_snapshot` captures exact lineage, immutable and idempotent | — | Planned | No known gap |
| STR-AC-020 | Downstream direct-table mutation and Draft reads rejected | 1 | Planned | Confirm no raw SQL/ORM Strategy-table access exists downstream |
| STR-AC-021 | Read access to Active plan without Approver assignment ≠ approval-task access | — | Planned | No known gap |
| STR-AC-022 | Portfolio counts/rows/routes/exports/reports/APIs share one predicate | 1 | Planned | Confirm in Phase 1 |
| STR-AC-023 | Default seed deterministic; second run no-op | 8 | Planned | — |
| STR-AC-024 | Missing ERPNext Fiscal Year fails seed, no fallback created | 8 | Planned | — |
| STR-AC-025 | 4 primary routes render without console error, match artboards | 6, 7 | Planned | — |
| STR-AC-026 | Loading/no-match/forbidden/server-error states disclose no false/unauthorised data | 7 | Planned | — |
| STR-AC-027 | Frappe header/breadcrumb reused, not duplicated; no PE/scope/context selector on any screen | 6, 7 | Planned | — |
| STR-AC-028 | No page/API accepts Value Commitment/source-ref/evidence/attachment/contact/baseline/treatment/actual-result/corrective-action data | 5, 9 | Planned | — |
| STR-AC-029 | Approver inspects exact submitted version across all 4 tabs, no Active-version substitution | — | Planned | No known gap |
| STR-AC-030 | Return/Approve available on every approval tab; reject stale version/status | — | Planned | No known gap |
| STR-AC-031 | No metadata/permission/route/service/seed/test refers to retired roles or statuses | 1, 4, 9 | Planned | `Strategy Viewer` is the known live violation (STR-401..404) |
| STR-AC-032 | Every write authorised through Active URA; no User Permission/capability/scope-assignment participates | — | Planned | Already satisfied by CU-3xx; confirm in Phase 1 and Phase 9's AUTH contract suite |
| STR-AC-033 | No `procuring_entity`/`procuring_entity_id`/`owner_org_unit_id`/KenTender `FinancialYear` reference anywhere | 2, 3, 9 | Planned | Direct gaps: STR-201/202 (schema), STR-301 (service payload) |
| STR-AC-034 | Strategy Author/Approver registered Site-wide; no command performs an OU scope check | 2 | Planned | Role registration done (CU-3xx); OU scope check removal is STR-204 |

## §14 seed-contract cross-reference

STR-CHG-001 v1.6 §18 names two other documents needing a matching correction as part of this change: **PLN-CHG-001** (Strategic Objective selection must consume `list_strategy_objectives`/`create_strategy_snapshot` with no PE/OU argument) and **BUD-CHG-001** (Strategy node/target references must carry no PE/OU scope). Neither is in this tracker's scope to edit, but Phase 3's `resolve_strategy_context()` correction and Phase 5's dead-code removal from `strategy_contracts.py` (which Budget's `loadTargetOptions` depends on) directly affect both modules' consumer code. Cross-reference note only — raise with each module's own tracker owner before Phase 3/5 land.
