# Procurement Planning — outstanding follow-ups

Items deliberately left open at the close of the **PLN-CHG-001 v1.2** rebuild
(Phases 0–12, closed 31 August 2026). Each is either an owner decision the
rebuild had no authority to make, a gap in a sibling module's own contract, or
a defect class with no live surface in MVP-1. Nothing here blocks the module's
acceptance contract; FU-01's §14.9 acceptance row (PLN-AC-046) was resolved
by retirement, not by the remediation this file originally described (see
below).

**Status:** re-annotated 9 September 2026: FU-10 and FU-11 closed — the Strategy §14.3 seed and the Budget line ownership both landed (independently of this file) as part of the SEED-OPS-001 canonical-seed work, and are confirmed here rather than by that work's own record. Verified clean, single-PE (no `PE-CGKIS`, no legacy orchestrator): `kentender_procurement.departmental_needs.seeds.kentender_mvp_r1.upsert_departmental_needs` then `kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.upsert_planning_base` on a `make seed-canonical THROUGH=budget` world; `test_planning_seed` 7/7 OK; `planning-release-evidence.spec.ts` 4/4 passed (rerun after `reset_planning_seed` + a fresh, non-idempotent rebuild, to rule out drift from the long-lived dev site's accumulated state). Fixed two spec assertions along the way (`planning-release-evidence.spec.ts:71,77`) that had gone stale under PLN-CHG-001 v1.13's two-item harmonization but were never exercised, because the spec had skipped itself on FU-10/FU-11 since it was written. Earlier note, re-annotated 7 September 2026: FU-07 closed by REQ-CHG-001 v1.6's cutover slice (the Requisitions module's own contract now exists and names its calling principal). Earlier note, re-annotated 5 September 2026 at the close of the SEED-001 v1.0 harmonized-fixture cutover: FU-01 is resolved by retirement (§1.1 removes the PE-KEBS fixture world outright rather than building the authoritative KEBS Budget Line/Strategic Objective this file previously called for). Earlier note at the close of the v1.12 correction cycle (FU-08..FU-11 added; FU-02 and FU-06 closed by v1.12). Earlier note from the cycle start: annotated 5 September 2026 at the start of the v1.12 correction cycle (`IMPLEMENTATION_TRACKER.md`): FU-02 and FU-06 are closed by that cycle (D11 adds `reference` to the Budget contract; DES-13 now has an artboard and is built); FU-01, FU-03, FU-04, FU-05, FU-07 are carried unchanged. Reservation-related wording in FU-05/FU-06 is moot under v1.12 §7.3 (Planning holds no reservation).

## Register

| ID | Item | Severity | Owner |
|---|---|---|---|
| FU-01 | **Resolved by retirement (SEED-001 §1.1, 5 Sep 2026).** §14.9 KEBS seed profiles were blocked on no authoritative KEBS Budget Line or Strategic Objective; the PE-KEBS fixture world is now deleted outright rather than completed — `seed_kebs_profiles` and its static-contract test are removed | Closed | — |
| FU-02 | Budget/Strategy published contracts expose no human business reference — screens show raw hash ids for Budget Lines | Medium | `kentender_budget` (and `kentender_strategy` for path-only labels) |
| FU-03 | The KENTENDER_MVP_V1 full-stack validator crashes upstream of the Planning checks on the retired `Strategy Programme` doctype | Medium | `kentender_strategy` / `kentender_core` seeds |
| FU-04 | Dormant references to retired Planning doctypes survive in tender-management and legacy seed families | Medium — latent crash-on-call, no live caller | `kentender_procurement` (tender-management), `kentender_core` legacy seeds |
| FU-05 | A successor's frozen governance snapshot cannot distinguish a carried-over item from one proposed for removal (no `item_state` in `_build_snapshot`) | Low — no UI trigger for removal exists in MVP-1 | `kentender_procurement` (Planning) + a design decision |
| FU-06 | `RemovePlanItemInSuccessor` / `CancelPlanUpdate` / `RetryPublication` have no UI trigger; PLN-DES-13 (Publication Result screen) deliberately not built | Low — service layer complete and tested | Design authority (next PLN revision) |
| FU-07 | **Closed (2026-09-07, REQ-CHG-001 v1.6).** The drawdown commands were System-Manager-gated pending a real Requisitions role vocabulary; `record_requisition_drawdown`/`reverse_requisition_drawdown` now require Head of Procurement Function, and the eligibility read gate widened to every registered Requisitions-caller role, OU-scoped roles checked against the Plan Item's own contributing departments. Evidence: `kentender_procurement.procurement_planning.tests.test_plan_requisition` Ran 22 tests OK, incl. `TestRequisitionCallerReadGate` and the HOPF-gated drawdown cases | Closed | — |
| FU-08 | PLN-CHG-001 v1.12 §14.5's illustrative milestone dates (23 May → 23 Jun evaluation) imply a 31-day evaluation period, above the governed 30-day ceiling of §4.9 / PLN-AC-114; the seed derives its baseline from the governed defaults PLN-DES-09 shows (1 May, 22 May, 21 Jun, 26 Jun, 28 Jun, 12 Jul, 31 Aug) | Low — a spec table to correct at the next PLN revision | Design authority (next PLN revision) |
| FU-10 | **Closed (2026-09-09).** The §14.3 Strategy prerequisite (Objective "Strengthen interoperable national digital health services") now resolves Active on the one-site model — STR-CHG-001 v1.7's correction (closed 2026-09-06) supersedes the Planned/superseded STR-802 state this row described. Verified: the Strategy Node's plan version status is `Active`; `verify_prerequisites()` no longer throws | Closed | — |
| FU-11 | **Closed (2026-09-09).** The §14.3 Budget prerequisite's Line Version ownership is fixed: `kentender_budget/seeds/kentender_mvp_v1_portfolio.py` now resolves `MOH-BL-DHI-2027`'s `owner_org_unit` dynamically via the same `(Grace, "Departmental Author", "Digital Health")` lookup the shared register uses, instead of the legacy `MOH-DIR-DHP` unit code; `MOH-BL-HWD-2027` is deliberately Entity-wide. No mismatch is possible by construction now. This does **not** require the legacy multi-PE orchestrator (`make seed-kentender-mvp-v1`) at all — see the corrected verification note below | Closed | — |
| FU-12 | Three acceptance rows are Partial after v1.12 Phase 8: PLN-AC-097 (county resident-tenderer advisory exists in `plan_readiness` and the editor control but no county-entity site fixture exercises it end to end), PLN-AC-101 (`item_status` exists; an optional Project Name on the plan header is not modelled — §4 defines no field for it), PLN-AC-110 (§7.5A's seven-return field-by-field verification is asserted only through the OCDS payload / Third Schedule tests, not as its own table-driven test) | Low | `kentender_procurement` (Planning) + design authority for the Project Name field |
| FU-09 | §14.2 names Peter Kimani's Digital Health assignment as split (ending 25 Nov 2026, successor from 1 Dec) with Julia acting 26–30 Nov; the shared KT-STD-001 §8.3 register seeded by `kentender_core.seeds.site_setup` holds Peter permanently and Julia acting 1 Oct–30 Nov, and the Planning seed verifies rather than re-grants the shared register (§14.2) | Low — a register alignment across NDS and Planning | `kentender_core` site seed + KT-STD-001 §8.3 |
| FU-13 | **Closed (2026-09-07).** PLN-DES-01's "actionable" card defaulted its title to "Your work" for mixed-kind work (falling back to "Ready to consolidate" only when every row is that one kind). Relabelled to "Actions" — a cross-module product decision to drop possessive framing on every module's landing-page queue title (NDS "My needs"→"Departmental Needs", Requisitions "Your Requisitions"→"Requisitions", Strategy "My work" tab→"Actions"), not a PLN-DES-01 correction. `WorkspaceScreen.spec.js`'s two assertions on the string updated; PLN-DES-01's own fidelity artboard shows the unaffected "Ready to consolidate" state, so `planning-fidelity.spec.ts` needed no change | Closed — cosmetic | — |

---

### FU-01 — §14.9 KEBS profiles blocked on missing authoritative fixtures (resolved by retirement)

**Resolved 5 September 2026, by retirement rather than by the remediation
originally described below.** SEED-001 v1.0 §1.1 reconciles the fictitious
second Procuring Entity `PE-KEBS` into the real one-site Ministry of Health
world instead of completing it: `seed_kebs_profiles` (the permanent
by-design `frappe.throw` stub this row used to describe), its sole caller
`test_the_kebs_profiles_fail_loudly_by_design`, `kentender_core.seeds.
kebs_foundation`, and the KEBS content in Departmental Needs'
`departmental_needs/seeds/profiles.py` are deleted outright, not extended.
`PLN-AC-046` is closed on that basis — there is no longer a KEBS acceptance
row for Planning to satisfy.

Original text, kept for record: `seed_kebs_profiles` failed loudly by
design: PE-KEBS existed (the `kebs_foundation` seed created PE/FY/OU/context
only), but a funded, submitted, accepted KEBS DPP — the prerequisite for
forming `PPI-KEBS-2026-ICT-001` — required a KEBS Budget Line and a KEBS
Strategic Objective that Budget's and Strategy's approved seed contracts
never provided, and §14.1 forbade Planning inventing either.

### FU-02 — no human business reference in the Budget/Strategy contracts

`list_eligible_budget_lines` / `list_strategy_objectives` expose an internal
hash `id` and a free-text `title`; Budget Line's own `generated_reference`
(e.g. `MOH-BL-DHI-2027`) is never returned. Every screen that must display a
Budget Line therefore shows the raw hash (visible on DES-02/03/09 evidence
screenshots). Cross-cutting — affects the Phase 4 DPP screens and Phase 6
editors alike (tracker finding 14). Fix belongs in the owning contracts, not
in per-screen lookups that would bypass them.

### FU-03 — full-stack validator blocked upstream of the Planning checks

`validate_kentender_mvp_v1` crashes at its Strategy section
(`frappe.db.exists("Strategy Programme", …)` — a doctype the Strategy rebuild
retired) before it can reach the Planning checks Phase 11 wired in at the
end. The Planning checks run green when called directly
(`kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.validate_planning_seed`).
The Strategy-era section needs its own v1.x rewrite by its owner.

### FU-04 — dormant retired-doctype references in sibling code

Planning's Phase 1 dropped the nine Demand-era doctypes **and their tables**;
`frappe.db.exists`/`get_value` against them now raises. One LIVE caller was
found and fixed at the Phase 12 cross-module checkpoint (Budget's
`_plan_item_label` — every Budget position read that met a reservation
crashed). Still-referencing but dormant paths, each reachable only from a
retired flow:

- `kentender_procurement/tender_management/services/export_tender_evidence.py`,
  `planning_tender_handoff_configuration.py`, `planning_tender_handoff_audit.py`
  and `doctype/tm2_tender/tm2_tender.py` — the Demand-era handoff chain; the
  tender-management rebuild owns their replacement.
- `kentender_core/seeds/demo_platform_seed/*`, `stable_platform_seed/purge.py`
  (doctype-guarded), `dev_full_reseed.py`, and the `_scn_*` scenario blocks of
  `seeds/kentender_mvp_v1/validate.py` (reached only via non-default flags).

### FU-05 — successor snapshot carries no item state

Tracker finding 26. An approver reviewing a plan update sees an
undifferentiated frozen item list; no artboard defines a "successor under
review" composition. Needs a design decision before any code.

### FU-06 — commands with no UI trigger

`RemovePlanItemInSuccessor`, `CancelPlanUpdate` and `RetryPublication` are
built, §8.2-complete and fully tested at the service layer, and PLN-DES-13
was deliberately not built (tracker PLN-902: the sandbox destination's only
reachable outcome is already surfaced on DES-14's governance card). A future
PLN revision that defines their compositions can wire them without touching
the services.

### FU-07 — drawdown commands authorised as system principal

`record_requisition_drawdown` / `reverse_requisition_drawdown` accept only
System Manager/Administrator because no Requisitions role vocabulary exists
in this repository to authorise against (§2.1). When the Requisitions module
lands, its contract should name the calling principal and these two gates
should adopt it.

## Verifying a fix

- **FU-01:** Closed by retirement, not by a build — `seed_kebs_profiles` no
  longer exists (SEED-001 §1.1); PLN-AC-046 → Done on that basis.
- **FU-02:** the owning contract returns a `reference` field; DES-02/03/09
  screens display it; re-capture the affected evidence screenshots.
- **FU-03:** `bench --site <site> execute kentender_core.seeds.kentender_mvp_v1.orchestrator.validate_kentender_mvp_v1`
  completes and its report contains the `planning.v12.*` checks, all passing.
- **FU-04:** repo-wide grep for the nine retired doctype names returns only
  history/docs; the tender-management suites still pass.
- **FU-05/FU-06:** a design artboard exists first; then the snapshot/UI work
  cites it.
- **FU-08:** the §14.5 table lists dates a 30-day evaluation period can produce, or §4.9 changes the ceiling; `seeds/kentender_mvp_v1.ITEM_VALUES` then follows.
- **FU-09:** `site_setup.ASSIGNMENTS` carries the split Peter/Julia dates and NDS's Julia acting-window tests still pass.
- **FU-12:** a county-entity site fixture drives the county advisory in a browser spec; §4 gains (or explicitly omits) the Project Name field; a table-driven test walks §7.5A's seven returns against `publication_payload.build_payload`.
- **FU-10/FU-11:** **Closed (2026-09-09).** Verified clean, single-PE, without the legacy multi-PE orchestrator: `make seed-canonical THROUGH=budget` (SEED-OPS-001, PE-MOH only), then `bench --site <site> execute kentender_procurement.departmental_needs.seeds.kentender_mvp_r1.upsert_departmental_needs --kwargs '{"commit": True}'`, then `bench --site <site> execute kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.upsert_planning_base --kwargs '{"commit": True}'` — `verify_prerequisites()` no longer throws; `test_planning_seed` 7/7 OK; `npx playwright test tests/ui/smoke/planning/planning-release-evidence.spec.ts --workers=1` 4/4 passed (confirmed again after `reset_planning_seed` + a fresh non-idempotent rebuild). `make seed-kentender-mvp-v1` is neither required nor recommended for this — it reintroduces `PE-CGKIS` and the legacy persona world that SEED-OPS-001 retires.
- **FU-13:** already closed — `npx vitest run --project procurement-planning` for `WorkspaceScreen.spec.js` is green with the "Actions" assertions, confirmed live in a browser as Grace Wanjiku.
- **FU-07:** the Requisitions contract names its principal; the two gates
  check that role and `test_plan_requisition`'s masking test uses it.
