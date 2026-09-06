# Strategy Alignment — gap analysis against STR-CHG-001 v1.6

**Authority:** `KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_6.md` (approved 3 September 2026; supersedes v1.5 and all earlier versions in full).
**Companions:** `03_STR_Rebuild_Implementation_Plan.md`, `IMPLEMENTATION_TRACKER.md`, `FOLLOW_UPS.md`.
**Analysis date:** 2026-09-03
**Implementation under review:** `kentender_strategy/kentender_strategy/` (doctypes, services, api, seeds, tests, public/js).

## 1. Executive summary

This is **not** a greenfield rebuild. Commit `ccff1b80` ("feat(strategy): CU-3xx — Strategy onto AUTH-ADR-001 v1.6") landed on 2026-09-03, the same day v1.6 was approved, and already delivered the hardest part of this document's intent: both Strategy roles registered site-wide in `kentender_core`'s business-role registry, `strategy_authorization.py` rewritten onto the real `authorise_record()`/`User Responsibility Assignment` mechanism (no User Permission, no capability profile), PE parameters stripped from most service signatures, the leftover "Strategy Manager" role deleted, and 64 tests across 7 `test_str_chg_001_phase*` suites updated and green.

What remains is a **correction pass closing specific, well-bounded gaps** the CU-3xx commit did not reach: two schema fields still present when the spec requires their absence, one field not renamed, one service contract whose shape and return payload don't match §7/§8 literally, one role the spec disposes of that's still live, a large body of dead code referencing deleted concepts, one piece of business logic (STR-BR-004 overlap) that needs semantic rewriting rather than a field strip, an unverified UI route architecture, and seed cleanup. Every item below was verified against the live tree — either by direct file read or by a Plan-agent research pass — not assumed from the spec text alone.

Verdict: correction in place, following the same posture STR-CHG-001 v1.6 §1 states for itself — no alias, no compatibility layer, no dual read.

## 2. What CU-3xx already delivered (verified — do not re-plan as new work)

| # | Item | Evidence |
|---|---|---|
| 1 | `Strategy Author` / `Strategy Approver` registered `Site-wide` in the business-role registry | `kentender_core/kentender_core/services/business_role_registry.py:177-178` |
| 2 | `strategy_authorization.py` rewritten onto `kentender_core.services.authorization.authorise_record(user, business_role, organisation_unit="", purpose=PURPOSE_COMMAND)` — real URA records, no User Permission | `kentender_strategy/kentender_strategy/services/strategy_authorization.py`; `require_plan_version_capability()`, `require_plan_create_capability()` |
| 3 | No-self-approval enforced from the version's own audit history, not a role comparison | `strategy_authorization.py::_blocked_by_self_approval`, raises `AUTH_SEGREGATION_BLOCKED` |
| 4 | `Performance Target.financial_year_id` Link **options** repointed from a bespoke doctype to ERPNext `Fiscal Year` | patch `cu_305_repoint_performance_target_fiscal_year.py` |
| 5 | Leftover "Strategy Manager" role hard-deleted | patch `str_chg_001_v1_7_delete_strategy_manager_role.py` |
| 6 | `kentender_procurement`'s `strategy_gateway.py` updated to call the new no-arg-shaped `resolve_strategy_context()`; contract test pinned | `kentender_procurement/kentender_procurement/procurement_planning/services/strategy_gateway.py`, `tests/test_gateway_contracts.py` |
| 7 | Two-PE (`PE-MOH`/`PE-CGKIS`) default seed made inert | `seeds/kentender_mvp_v1_strategy.py::upsert_kentender_mvp_v1_strategy` returns `{"ok": False, "superseded": ...}` before reaching its old body |
| 8 | Site-wide fixture actor for the cutover | `mercy.kilonzo@moh.example.test`, `Strategy Author`, via `kentender_core/kentender_core/seeds/site_setup.py` |
| 9 | Budget/Procurement demo fixture (`works_master_strategy_hierarchy.py`) rebuilt onto `responsibility_administration.grant()`, site-wide | same file, `fixture_namespace="works-master-strategy"` |
| 10 | 64 tests across 7 suites updated for the cutover | `kentender_strategy/kentender_strategy/tests/test_str_chg_001_phase1..7_*.py` |
| 11 | New v1.6-aligned artboard set on disk, replacing the old space-named 20-file set | `docs/mvp-1-r1/02_strategy/strategy_design/STR-DES-01..10.dc.html`, `Shell.dc.html`, `index.dc.html` (dated 2026-09-03, untracked) — not yet verified against a fidelity gate |

## 3. §1.1 disposition register — row-by-row verdict against current code

Only the rows with live schema/service/permission relevance are checked (the design-doc-only dispositions from v1.5 — PVOs, treatment, Strategic Outcome, etc. — were already resolved by an earlier generation; confirmed absent as doctypes, see §5 below).

| Spec disposition | Present in code? | Evidence | Verdict |
|---|---|---|---|
| `procuring_entity_id` on `StrategicPlan` — **remove** | **Yes — violated** | `strategic_plan.json:53-62` — field present, `hidden=1, read_only=1`, description literally says "Column retained until the removal phase" | Delete field |
| `pe_fy_context` on `StrategicPlan` — implied by the same removal (denormalised PE data) | **Yes — violated** | `strategic_plan.json:64-73` — same hidden/read-only/deprecated pattern | Delete field |
| `owner_org_unit_id` on `StrategicPlan` — **remove** | **Yes — violated, and live** | `strategic_plan.json:75-81` — no `hidden`/`read_only`, fully active, `search_index: 1` | Delete field; rewrite the one function that reads it as a live filter |
| Frappe Roles + PE/OU User Permissions as the authorization mechanism — **remove** | No — compliant | `strategy_authorization.py` confirmed onto `authorise_record()` | Already done (CU-3xx) |
| `financial_year_id` → `fiscal_year` (ERPNext `Fiscal Year`) | **Partly — field name unchanged** | `performance_target.json` still names the field `financial_year_id`; only its Link `options` were repointed (item 4, §2 above) | Rename the field itself |
| §9 "prefer exact OU scope over PE-wide scope" precedence rule — **remove** | No — compliant | No such precedence logic found; `resolve_strategy_context` rejects ambiguity rather than preferring | Already compliant |
| County Government of Kisumu seed plan, its 3 actors, cross-PE isolation tests — **remove entirely** | **Partly — dead code remains** | `kentender_mvp_v1_strategy.py`'s `upsert_...` function is stubbed inert, but ~120 lines of `PE_MOH`/`PE_CGKIS`/actor-email dataset definitions remain in the file body as unreachable text | Delete the dead body |
| Bespoke fixture cast (`str.author.moh@…` etc.) → shared KT-STD-001 §8.3 register | **Not yet added to KT-STD-001** | `KT-STD-001` §8.3 does not yet list Esther Muthoni / Dr Alfred Ochieng / Naomi Chebet | Add per §14.1 (cross-doc correction, §18) |
| Fixture timeline 15–16 Mar 2027 → 24–25 Nov 2026 | Not verified live | Old dead seed body still carries old-generation dates; the two functions that generate the STR-DES v2 artboard fixture (`seed_str_des_v2_fixture`/`teardown_str_des_v2_fixture`) are reachable but call orphaned dependencies | Rebuild per §14.4 |
| PE row on STR-DES-01/02/03/06 artboards — **remove** | Not yet verified against the *new* artboard set | New artboards exist on disk (§2 item 11) but haven't been checked against §11's exact content | Verify in Phase 7 |
| "existing KenTender PE/FY selector" in §12.1/§12.12 — **remove** (component no longer exists) | Compliant | No such selector found in Strategy's Vue components | Already compliant |

## 4. Domain model diff (§4)

### 4.1 `StrategicPlan` field-by-field

| Current field | Spec disposition | Gap |
|---|---|---|
| `plan_id` | Keep | None |
| `title` | Keep | None |
| `procuring_entity_id` | **Delete** | Live, hidden+read-only (see §3) |
| `pe_fy_context` | **Delete** | Live, hidden+read-only (see §3) |
| `owner_org_unit_id` | **Delete** | Live, fully active (see §3) |
| `plan_role` | Keep | None |
| `parent_primary_plan_id` | Keep | None |
| `period_start` / `period_end` | Keep | None |
| `fixture_namespace` | Keep (test-seed scoping, not user data) | None |

### 4.2 `PerformanceTarget` field-by-field

| Current field | Spec disposition | Gap |
|---|---|---|
| `financial_year_id` | **Rename to `fiscal_year`**, Link target already ERPNext `Fiscal Year` | Field name unchanged |
| `target_by_date`, `comparison`, `target_value`, `indicator_id`, `target_id` | Keep | None |

### 4.3 `StrategyAuditEvent` (§4.6)

Not implemented as a dedicated doctype — deliberately. `strategy_audit.py:1-9` documents a prior decision that a bespoke `Strategy Audit Event` doctype is "a known duplicate mechanism, not a pattern to follow," and `test_str_chg_001_phase1_domain_model.py` explicitly asserts `frappe.db.exists("DocType", "Strategy Audit Event")` is `False`. Every §4.6 field is threaded through the shared `kentender_core.services.audit_event_service.log_audit_event` **except one**: the "exercised responsibility assignment ID" is recorded as a capability label string (`strategy_transitions.py`/`strategy_writes.py` pass `TRANSITIONS[key]`'s capability constant into `record_event(capability=...)`), not `decision.assignment.name`, the real URA record ID that `strategy_authorization.py`'s `authorise_record()` call already resolves and returns.

**Decision (resolved with the module owner, recorded in the tracker):** keep the shared-service approach; thread the real assignment ID through. No new doctype.

### 4.4 Other doctypes

`Strategic Plan Version`, `Strategy Node`, `Performance Indicator` match §4.2–§4.4 field-for-field; no gap found. `Strategy Command Journal` (idempotency ledger) is not a v1.6-named entity but is an internal mechanism, not user-facing data — no disposition applies.

### 4.5 Legacy/disposed doctypes — confirmed absent

Plan Value Commitment, Strategy Value Commitment (+ Link), Public Value Objective, Strategic Outcome, Strategy Corrective Action, and any treatment/planned-treatment/treatment-questionnaire doctype: **none exist** as DocType JSON files anywhere in the repo. They survive only as:
- Historical patch scripts documenting their removal (`patches/str_chg_001_phase1_domain_model_rebuild.py`, `str_chg_001_phase8_remove_strategic_outcome.py`, `mvp1_teardown_drop_legacy_strategy_doctypes.py`).
- **Dead, still-importable code** in `services/strategy_contracts.py` — `list_strategy_value_commitments()` queries `"Strategy Value Commitment"`/`"Strategy Value Commitment Link"`/`"Strategic Outcome"` by name; `_outcome_node()`; `get_plan_overview()` calls the value-commitments function. None of these three functions is reached from any live whitelisted API path (only 4 of `strategy_contracts.py`'s ~30 functions are imported anywhere: `_node_ancestor_path`, `build_strategy_reference`, `list_active_targets`, `validate_strategy_reference`, all via `strategy_consumer.py:23-28`). This is a real STR-AC-002 violation ("No executable metadata... refers to... Strategic Outcome... Strategy Corrective Action") — unreachable code is still executable metadata.
- `kentender_core/kentender_core/seeds/kentender_mvp_v1/validate.py:401,432` still probes `frappe.db.exists("Strategic Outcome", ...)` / `frappe.db.exists("Strategy Value Commitment", ...)` — harmless (asserting absence) but worth a pass in the static scan.

## 5. Service and command contract gaps (§7, §8)

### 5.1 `resolve_strategy_context()` does not match the §7/§8 shape

`services/strategy_consumer.py:38-129`, read directly:

- **Input**: signature is `(organisation_unit=None, effective_date=None)`. No `fiscal_year` input alternative (§7 requires "exactly one of `as_of_date` or `fiscal_year`"). No `include_supporting` flag — Supporting Frameworks are always returned unconditionally (§7 requires it default `false`, opt-in).
- **Supporting Framework filter still OU-keyed**: `_active_versions()` (line 62-93) applies `filters["owner_org_unit_id"] = organisation_unit` when resolving Supporting plans (line 64-65) — reads a field the spec requires deleted.
- **Return payload leaks scope data**: the function returns `"procuring_entity": frappe.db.get_single_value("Site Procuring Entity", "pe_code")` and `"organisation_unit": organisation_unit` (lines 114-115) — both a direct STR-AC-033 violation ("No `procuring_entity`... reference exists in Strategy... services") and a §7 violation ("contains only IDs, titles, role, period, version, status and the hierarchy summary").
- The whitelisted wrapper `api/strategy_consumer_api.py:39-48` additionally still accepts a `procuring_entity` kwarg it silently drops, described in its own comment as a "transport-compat bridge for pre-cutover callers" — a compatibility shim v1.6 §1 prohibits ("no compatibility layer").

### 5.2 `_assert_no_primary_overlap()` — STR-BR-004 enforcement has load-bearing OU logic

`services/strategy_transitions.py:98-130` (Plan-agent verified): docstring still reads "two Primary plans **for the same PE/OU**"; the body treats a PE-wide plan and an OU-scoped plan as non-overlapping unless both share `owner_org_unit_id`. v1.6's STR-BR-004 has no PE/OU qualifier at all — scope is site-wide, so *any* two overlapping-date Primary plans conflict. This needs a genuine logic rewrite, not a field-removal footnote: deleting `owner_org_unit_id` without rewriting the predicate either crashes on a missing column or silently changes what counts as a conflict.

### 5.3 Missing DB-level guard (§16.1)

§16.1 explicitly requires "a database-level partial unique index or equivalent guard in addition to the approval-transaction check" for STR-BR-004. No such index/constraint was found in the patches directory in the time available for this analysis — **flagged as unverified, not confirmed absent**. Phase 1 of the implementation plan must confirm before Phase 2 treats it as a gap.

## 6. Permission gaps (§6)

| Spec requirement | Today |
|---|---|
| Exactly two Strategy workflow responsibilities: `Strategy Author`, `Strategy Approver` | Both registered site-wide (done, §2 item 1) |
| "Read access is not a third Strategy workflow role" — `Strategy Viewer` disposed of in §1.1 | **Violated.** `Strategy Viewer` Role still holds live DocPerm read rows on all 5 domain doctypes (`strategic_plan.json:181-192` confirmed directly; Plan-agent found the same pattern on `performance_target.json`, `strategy_node.json`, `strategic_plan_version.json`, `performance_indicator.json`) plus the Page/Workspace JSONs |
| `Auditor` registered as a business role under AUTH-ADR-001 §4.4, confers no Strategy workflow action | Not verified whether `Auditor` is a registered business-role-registry entry or a bare Frappe Role in Strategy's own DocPerms — Phase 1 to confirm |
| No `kentender_scope_map` entry required in practice, since both roles are site-wide (§16.1 says register anyway) | **No entry exists.** CU-3xx's commit message records a deliberate decision not to add one: a map entry would `1=0` list access for a site-wide role under the current DocPerm-via-URA-projection gate, and separately, the ADR's own documented map shape (`{"DocType": {"ou_field": ...}}`) doesn't match the real merge code in `kentender_core/kentender_core/services/authorization.py` (which expects a flat string value per doctype) |

**Decision (resolved with the module owner, recorded in the tracker):** keep CU-3xx's `kentender_scope_map` non-registration as a documented deviation from §16.1's literal text; remove `Strategy Viewer` entirely per §1.1.

## 7. UI / route architecture (§10)

Current implementation is three classic Frappe Desk Pages, not literal path-segment routes:

| §10 canonical route | Current | Gap |
|---|---|---|
| `/app/strategy` (Portfolio) | `strategy-portfolio` page → `/app/strategy-portfolio` | Doesn't match |
| `/app/strategy/plan/{plan_id}` (Plan workspace) | `strategy-plan-workspace` page | Doesn't match |
| `/app/strategy/plan/{plan_id}/version/{version_number}/structure` | same page, sub-route parsed client-side via `useRouteState.js` | Doesn't match literally |
| `/app/strategy/approval/{plan_version_id}` | `strategy-review-task` page | Doesn't match |

`kt_cl_surface_registry.js:506-544` documents — for Strategy and three sibling Industry-design-system modules alike — that Vue-in-Desk pages calling `enterNative()` for their own sidebar/chrome must **not** be registered there, because registration lets the legacy Civic Ledger router repaint a second toolbar. Strategy's non-registration is therefore correct, not a gap.

One directly relevant precedent: Departmental Needs consolidated eight logical screens onto **one** Frappe Page matching its canonical top segment, with in-page sub-route parsing off `frappe.get_route()`. Strategy's `useRouteState.js` already does the same sub-routing mechanism inside three separate Pages. Whether v1.6 §10's "canonical route" requirement is satisfied by the current three-Page split, or requires single-Page consolidation matching the Departmental Needs pattern, **is not decidable from the spec text or code alone** — it needs a live route trace (does direct load of `/app/strategy-plan-workspace/{plan_id}` survive refresh/back-forward with the plan ID intact?) before a phase can be sized. Flagged as Phase 1 research, not resolved here.

## 8. Seeds and tests

- `seeds/kentender_mvp_v1_strategy.py`: the `upsert_kentender_mvp_v1_strategy()` short-circuit (CU-307) leaves ~120 lines of dead `PE-MOH`/`PE-CGKIS` dataset text in the file. Two functions **not** behind the stub — `seed_str_des_v2_fixture()` / `teardown_str_des_v2_fixture()` — are still reachable but call now-orphaned dependencies (they look up a plan by `procuring_entity_id=PE_MOH`, which nothing seeds anymore).
- `works_master_strategy_hierarchy.py` (Budget/Procurement demo fixture) was rebuilt this commit onto `responsibility_administration.grant()`, site-wide — confirmed clean, no gap.
- 7 test suites (`test_str_chg_001_phase1..7_*.py`, 64 tests) cover the CU-3xx cutover. None yet exercises: the corrected `resolve_strategy_context()` shape (§5.1 above), the rewritten STR-BR-004 overlap semantics (§5.2), the `Strategy Viewer` removal, or a repository-wide static scan for the full disposed-concept list (STR-AC-002, STR-AC-031, STR-AC-033).
- No Strategy design-fidelity gate exists yet — only System Setup has one (commit `9be512f3`). The three legacy Makefile targets (`ui-strategy-typography-gate`, `ui-strategy-alignment-ui-gate`, `ui-strategy-role-gate`) predate this gate pattern and their continued relevance against the new artboard set is unverified.

## 9. Documentation hygiene

- The stale citation `"STR-CHG-001 v1.5 §7"` at `business_role_registry.py:177-178` should be corrected to `v1.6 §6` in the same pass that touches this file.
- KT-STD-001 §8.3/§8.5 does not yet carry the three Strategy actors or the 24-25 Nov 2026 fixture instant — a required companion correction per v1.6 §18's document table.
- PLN-CHG-001 and BUD-CHG-001 both have a required correction row in v1.6 §18 (Strategic Objective selection / node references must carry no PE or OU argument) — out of this app's scope to edit, but worth a cross-reference note in the tracker so Planning's and Budget's own trackers pick it up.

## 10. Known decisions carried into the plan

All four resolved with the module owner on 2026-09-03; full rationale in the implementation plan's decision register and the tracker's decision log.

1. **`kentender_scope_map`** — keep CU-302's non-registration decision, document as a deviation from §16.1's literal text.
2. **`StrategyAuditEvent`** — keep the shared `audit_event_service`, thread the real assignment ID through to close the one field gap. No new doctype.
3. **Dead two-PE seed code** — delete it entirely; rebuild the STR-DES v2 artboard-fixture generator off the live single-PE seed identity.
4. **Doc convention** — mirror NDS/Planning: `02_`/`03_` numbering, standalone gap-analysis doc, separate `FOLLOW_UPS.md`.

One item intentionally **not** resolved here: the UI route-architecture question (§7 above) is gated on Phase 1 research, not decidable from current evidence.
