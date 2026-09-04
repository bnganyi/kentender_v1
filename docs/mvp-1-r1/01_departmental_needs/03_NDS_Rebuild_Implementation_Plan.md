# Departmental Needs rebuild — implementation plan (v1.1 → v1.6)

**Authority:** `KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_6.md` (the single implementation authority; this plan sequences work against it and adds no new requirements).
**Companions:** `02_NDS_Rebuild_Gap_Analysis.md` (what is wrong today), `IMPLEMENTATION_TRACKER.md` (phase status, evidence, decision log).
**Status:** Phase 0 complete (gap analysis, this plan, tracker authored). Phases 1–10 not started.
**Author date:** 2026-09-04

## 1. Governing approach

Same workflow as the module's own v1.1 cycle and Budget's BUD-CHG-001 v1.3 cutover: research first, author plan + tracker, then execute phase by phase with the tracker's rows as the evidence ledger. No row is `Done` on inspection alone — each cites a command, test name, diff, or described screenshot.

This is a **correction in place against an already-working module**, not a rebuild from scratch. §1's posture is unchanged from v1.1: no alias, no redirect, no dual-read, no compatibility flag. Where this plan says "delete," the deletion lands in the same phase as its replacement — never deferred as future cleanup. §17's prohibited-shortcuts list (plus KT-STD-001 §10's universal list) is a standing constraint on every phase, not a final check.

Two existing assets are explicitly preserved, not rewritten from zero:

- `services/lifecycle.py`'s transactional pattern (idempotency key → row lock → optimistic token → authorization → state guard → validation → mutate → audit event → routed task dispatch) — only its authorization call sites change.
- The Vue-in-Desk/Industry frontend and its eight existing screens — only the PE dimension, the intake-window screen, and the unit source change.

## 2. Decision register

| # | Decision | Resolution | Phase | Why it needs recording |
|---|---|---|---|---|
| D1 (carried, unchanged) | Owning app / module boundary | Departmental Needs stays a module inside `kentender_procurement`, separate from Procurement Planning. Planning consumes Accepted Needs only through the published event contract; direct access to Needs DocTypes/tables/internal services stays prohibited and architecture-tested (`test_departmental_needs_architecture.py`). | — | Firm Project Owner decision from the v1.1 cycle; nothing in v1.6 revisits it. Restated so it isn't re-litigated. |
| D2 (**reversed** from v1.1) | Authorization mechanism | Replace native Frappe Role + User Permission with the AUTH-ADR-001 v1.6 resolver (`kentender_core.services.authorization.authorise_record`/`require_responsibility`) backed by `User Responsibility Assignment`, matching Budget's and Strategy's already-migrated pattern. | 2 | v1.1's decision compared against the *legacy* `authorization_policy`/Capability-Profile engine, not today's resolver — see Gap Analysis §5. NDS-CHG-001 v1.6 §6 and its own §16.4 correction-slice checklist are unambiguous and controlling. |
| D3 | `Needs Intake Window` doctype | **Delete outright.** Replace with read-only consumption of `Fiscal Year.kentender_needs_submission_open`/`_closes_at` (already shipped by `kentender_core/install.py`) via `kentender_core.services.site_configuration`. | 1 | §4.1/§16.4.11/§17 forbid NDS owning any part of the flag; the fields and admin commands already exist centrally. |
| D4 | `procuring_entity` field | Removed from every NDS doctype and every published payload. | 1 | Site is implicitly one PE (AUTH-ADR-001 v1.6 §1.1); NDS §4 carries no PE field in its v1.6 domain model. |
| D5 | Fiscal Year source | `Departmental Need.financial_year` retargets from KenTender's own `Financial Year` doctype to ERPNext's native `Fiscal Year`. | 1 | NDS-CHG-001 v1.6 §3, §16.2, §16.4.11 — remove all `PE Fiscal Year Context` reads along with it. |
| D6 | Unit source | `Departmental Need Version.unit` retargets from KenTender's own `Unit Of Measure` doctype to ERPNext's native `UOM` (`enabled=1`). | 1 | v1.6 §1.1 "New in v1.6"; corrects a v1.1-era defect (a native equivalent existed and was overlooked when `Unit Of Measure` was built). |
| D7 | Field naming | Keep existing plain Link field names (`organisation_unit`, `financial_year`, `unit`); do not rename to match v1.6 prose's `_id` suffixes. | 1 | Matches `User Responsibility Assignment`'s own field-naming convention (also defined in AUTH-ADR-001 v1.6) and every sibling module. A literal rename would be pure churn with no behavioural or contractual benefit. |
| D8 (carried, unchanged) | Frontend stack | Stays Vue-in-Desk on the Industry design system, unregistered from `kt_cl_surface_registry.js`/`STITCH_DESK_SURFACES`. | 5 | Confirmed deliberate, documented convention shared by every Industry-design sibling (Budget, Strategy, Planning, System Setup); overrides the generic AUTH-ADR-001 §14.5 instruction, as already recorded elsewhere in the repo. |
| D9 | Acting-HoD mechanism | Move from "same role + time-bound scoped User Permission (existence = time bound)" to one `User Responsibility Assignment` row with `appointment_type = Acting`, `effective_from`/`effective_to`, required `authority_reference`. | 2 | AUTH-ADR-001 v1.6 §4.5 models Acting as a real, auditable, dated record rather than a presence/absence check. |
| D10 | AUTH_* vs NDS_* error codes | Departmental Needs keeps its own closed §9 error-code set. Service-layer code catches `ResponsibilityError`/its `.code` from the resolver and remaps to the matching `NDS_*` code via the module's existing `errors.py::fail()`; no raw `AUTH_*` code reaches a client. | 2 | AUTH-ADR-001 v1.6 §10 describes its codes as "the shared vocabulary of the resolver, not a replacement for a module's published error contract." |

## 3. Phase sequence

Each phase lists its exit condition. Detailed per-item rows live in `IMPLEMENTATION_TRACKER.md`.

### Phase 0 — Plan and tracker *(complete)*
Author `02_NDS_Rebuild_Gap_Analysis.md`, this plan, and reset the tracker. Light-touch annotation of `FOLLOW_UPS.md` (FU-11 now resolved by this rebuild rather than open; FU-06 remains open — v1.6 adds no pipeline-count contract).

### Phase 1 — Domain model
- Delete `Needs Intake Window` doctype, its table (patch), and every schema reference (D3).
- Remove `procuring_entity` from `Departmental Need`, `Departmental Need Review Task`, `Departmental Need Decision`, and the `DepartmentalNeedAccepted.v2` payload builder (D4). Patch to drop the column; static scan proving absence.
- Retarget `Departmental Need.financial_year` from KenTender's `Financial Year` to ERPNext's `Fiscal Year` (D5). Update every query/report that joins on the old doctype.
- Retarget `Departmental Need Version.unit` from KenTender's `Unit Of Measure` to ERPNext's `UOM`, filtered `enabled=1` (D6). Retire the custom doctype once nothing references it.
- Delete the three empty leftover directories (`departmental_need_attachment/`, `departmental_need_item/`, `departmental_need_review/`) — filesystem cruft from the v1.1 cutover, already dropped from the DB.
- Bump `kentender_core/services/business_role_registry.py::REGISTRY`'s citation for `Departmental Author`/`Head of User Department` from `NDS-CHG-001 v1.4` to `v1.6`; confirm `Procurement Planner` (Site-wide) and `Auditor` entries exist.

**Exit:** schema matches NDS-CHG-001 v1.6 §4 exactly (no `procuring_entity`, no `Needs Intake Window`, Fiscal Year/UOM retargeted); clean `bench migrate` on the target site; static scan proves the three removed concepts absent.

### Phase 2 — Services and authorization
This phase executes NDS-CHG-001 v1.6 §16.4's 13-step checklist directly (see Gap Analysis §5 for the full step-by-step mapping); it is not re-derived here.

- Rewrite `services/permissions.py` onto `kentender_core.services.authorization.authorise_record`/`require_responsibility`, `User Responsibility Assignment`, and `descendants_of` for OU-subtree checks (D2). Remove every `frappe.get_all("User Permission", ...)` call.
- Rewrite `services/context.py`: remove `PE Fiscal Year Context` reads and the custom `Financial Year` resolution entirely; read the Needs-submission flag via `kentender_core.services.site_configuration`; implement `list_need_create_targets()` (Departmental Author OU assignments × the one open-flagged Fiscal Year) and a filter-only `selectable_financial_years()`.
- Update `services/my_work_provider.py` and `services/notifications.py` call sites onto the new `permissions.py` surface.
- Implement acting-HoD via `User Responsibility Assignment(appointment_type=Acting, ...)` (D9); remove the scoped-User-Permission mechanism.
- Map `ResponsibilityError`/AUTH_* codes onto the module's own `NDS_*` set at the service boundary (D10).
- Add the Cartesian-product OU-isolation regression (§16.4 step 8: Grace as Author in one OU and acting HoD in another must never cross) and the parent-OU-covers-descendants-not-siblings test (step 10).

**Exit:** every §16.4 step evidenced; zero `User Permission`/`PE Fiscal Year Context` reads remain in Departmental Needs code; every scoped read/command routes through the shared resolver.

### Phase 3 — API and command surface
- Rename `resolve_needs_contexts` → `resolve_needs_scope`, reshaped onto assignment/OU-scope output, PE removed.
- Add `list_needs_financial_years`, `list_need_create_targets`, `get_needs_submission_state` (read-only, sourced from `site_configuration`).
- Delete `get_needs_intake_window` and `save_needs_intake_window` outright — no replacement write command exists in Departmental Needs (System Setup owns the write).
- Confirm the §8.2 command set's existing whitelisted names are unchanged; update each command's internal authorization call to the Phase 2 surface and drop any PE parameter from its signature/payload.

**Exit:** whitelisted contract set matches NDS-CHG-001 v1.6 §8.1/§8.2 exactly (tested by name equality, matching the existing `test_every_read_contract_is_whitelisted_under_its_exact_name` pattern); no writable DocType endpoint bypasses a command.

### Phase 4 — Planning integration payload check
- Confirm `DepartmentalNeedAccepted.v2`, `DepartmentalNeedSuperseded.v1`, `DepartmentalNeedWithdrawn.v1` payload builders drop `procuring_entity` and otherwise still match §7.1 exactly (OU + FY id, title/description/expected-result, quantity/unit, required-by date, content hash).
- Cross-app check: grep the whole repo for real consumers of the `procuring_entity` field in the current payload before removing it (Procurement Planning is the only consumer; confirm via `procurement_planning/services/needs_intake.py`).
- No outbox mechanism change — `Departmental Need Event`'s transactional-outbox delivery is unaffected.

**Exit:** contract tests green on all three events with the corrected field set; no Planning-side code references the removed PE field.

### Phase 5 — Frontend
- Remove the PE dimension from `ContextPicker.vue` (and the `kt_working_procuring_entity` user-default it reads); keep OU (and Fiscal-Year-flag awareness) only.
- Delete `IntakeWindowScreen.vue` and its `/intake-window` route; replace any Fiscal-Year-flag display with a read-only line in the existing context strip, sourced from `get_needs_submission_state` (§11.11 — no NDS-owned configuration screen).
- Switch `NeedEditorScreen.vue`'s unit source to ERPNext `UOM`.
- Update NDS-DES-15 "Create need for" dialog behaviour to be driven by `list_need_create_targets`.
- Confirm no artboard-facing copy changes are needed (KT-STD-001 §2.2 fixture-context PE lines were never rendered in the first place; spot-checked against §11.2–11.16).

**Exit:** no PE control, selector or column on any screen (NDS-AC-058 equivalent); intake-window route returns 404/redirects to the workspace; production-mode asset build clean with the changed bundle's content hash verified.

### Phase 6 — Seeds and fixtures
- Rewrite `seeds/kentender_mvp_r1.py` and `seeds/profiles.py` to grant `User Responsibility Assignment` rows through the `kentender_core` administration command, not raw `User Permission` inserts.
- Align actors to KT-STD-001 §8.3: drop `amina.hassan@moh.example.test` from this module's fixtures, replace `auditor.moh@example.test` with `naomi.chebet@moh.example.test`, keep Grace/Peter/Julia/Mercy per §14.2's exact assignments.
- Seed against ERPNext `Fiscal Year` `2027-2028`, opened via `site_configuration.open_needs_submission`, instead of a `Needs Intake Window` record.
- Seed units from ERPNext `UOM` (`Programme`, `Each`), confirming both are `enabled=1`.
- Update `seeds/playwright_ui_fixtures.py` to the same actor/FY/unit changes.

**Exit:** seeds run twice with identical results (idempotent, per KT-STD-001 §8.6); §14 prerequisites and actor table satisfied exactly.

### Phase 7 — Permission, domain and lifecycle tests
- Rewrite `test_departmental_needs_permissions.py`: remove `User Permission` manipulation and cross-`PE-CGKIS` isolation tests; invert `test_the_module_consults_no_parallel_permission_store` to forbid `User Permission` as an authority source and require `kentender_core.services.authorization` usage; add the Phase 2 Cartesian-product and parent/descendant tests.
- Rewrite `test_departmental_needs_domain_model.py`: remove `procuring_entity`/intake-window assertions; add ERPNext-Fiscal-Year/UOM-Link assertions.
- Update `test_departmental_needs_lifecycle.py`, `test_departmental_needs_events.py`, `test_departmental_needs_contracts.py`, `test_departmental_needs_seed.py`, `test_departmental_needs_my_work.py`, `test_departmental_needs_audit_and_notifications.py` for the new field/contract shapes; no behavioural rewrite expected beyond field/authorization plumbing.
- Retire `departmental-needs-intake-window.spec.ts` and `departmental-needs-scheduled-window.spec.ts` outright; update the remaining five Playwright specs for the single-PE, resolver-backed context.

**Exit:** full module Python suite green; updated Playwright suite green (`npm run test:ui:smoke:nds`, single-worker per FU-01).

### Phase 8 — Static and architecture scans
Extend `test_departmental_needs_static_scan.py`'s prohibited-concept list to include `Needs Intake Window`, `procuring_entity`, the custom `Financial Year`/`Unit Of Measure` doctypes, and any remaining `User Permission`-as-authority read. Confirm `test_departmental_needs_architecture.py`'s D1 boundary guard is untouched and still passes.

**Exit:** static scan proves every retired concept absent from source, not just from the database; architecture guard green.

### Phase 9 — Full verification
- Full module suite (`bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.departmental_needs.tests.*`).
- Production-mode asset build (`./scripts/bench-with-node.sh build --app kentender_procurement` from the bench root) — closes the still-open v1.1 follow-up FU-02 opportunistically, since a rebuild of this size needs one anyway.
- Full Playwright suite, single-worker, with visual baselines re-shot (no PE row now present in any screenshot).
- Live browser walkthrough: golden path plus at least one interactive re-render, zero console errors, zero failed own requests.

**Exit:** KT-STD-001 §6's required release evidence satisfied in full for this change unit.

### Phase 10 — Acceptance sign-off
Map every NDS-CHG-001 v1.6 §15 acceptance criterion (NDS-AC-001–058) to its evidence; confirm §19 E2E-REQ-001 conformance; update `FOLLOW_UPS.md` with anything deliberately deferred; update project memory.

**Exit:** all applicable ACs evidenced Done in the tracker; nothing claimed without an observed result.

## 4. Files in scope

**Delete:** `doctype/needs_intake_window/`, `doctype/departmental_need_attachment/` `departmental_need_item/` `departmental_need_review/` (empty dirs), `public/js/departmental_needs/components/IntakeWindowScreen.vue`, `tests/ui/smoke/departmental_needs/departmental-needs-intake-window.spec.ts` and `-scheduled-window.spec.ts`, `kentender_core`'s `Unit Of Measure` doctype (once unreferenced), the module's own `Financial Year`-doctype read paths.

**Rewrite:** `departmental_needs/services/{permissions,context,my_work_provider,notifications}.py`, `doctype/departmental_need/`, `doctype/departmental_need_version/`, `doctype/departmental_need_review_task/`, `doctype/departmental_need_decision/`, `api.py` (read-contract surface only), `setup/departmental_needs_doctypes.py`, `seeds/{kentender_mvp_r1,profiles,playwright_ui_fixtures}.py`, `public/js/departmental_needs/components/ContextPicker.vue`, `public/js/departmental_needs/components/NeedEditorScreen.vue`, `tests/test_departmental_needs_{permissions,domain_model,static_scan}.py`.

**Touch (small, mechanical):** `services/lifecycle.py`, `services/usage.py`, `services/workspace.py`, `services/events.py` (drop the PE field from payload builders / query filters only), `kentender_core/services/business_role_registry.py` (citation bump), remaining Playwright specs, remaining Python test modules (field/contract shape only).

**Not touched:** `kentender_core/kentender_core/install.py`, `kentender_core/services/site_configuration.py` (already correct), the Frappe `Page`/route registration, `kt_cl_surface_registry.js`/`STITCH_DESK_SURFACES` (correctly absent), Procurement Planning's own authorization mechanism (out of scope — see Gap Analysis §10.2).

## 5. Verification commands

```bash
# focused Python test (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.departmental_needs.tests.<module>

# focused Playwright
npx playwright test tests/ui/smoke/departmental_needs/<spec>.spec.ts -g "<test name>"

# focused vitest
npx vitest run --project departmental-needs

# assets (from /home/midasuser/frappe-bench) — never plain `bench build`
./scripts/bench-with-node.sh build --app kentender_procurement

# bench lifecycle (from /home/midasuser/frappe-bench)
bench --site kentender.midas.com migrate
make validate-links && make clear SITE=kentender.midas.com
make seed-kentender-mvp-v1 SITE=kentender.midas.com
make seed-kentender-mvp-v1-validate SITE=kentender.midas.com
```

Per KT-STD-001 §5 and `CLAUDE.md`: red/green on the focused node first, then the affected group, then the module suite once. Do not rerun the whole repository suite after each small fix — Phase 2's authorization rewrite is shared infrastructure in the sense KT-STD-001 §5 means it, so its own release gate additionally requires the affected-module tests (Phase 7) and the cross-app architecture guard (Phase 8), not just a happy-path module test. After CSS/JS changes, clear the site cache and hard-refresh Desk before diagnosing a code defect; confirm the rebuild landed by checking the bundle's content hash changed.
