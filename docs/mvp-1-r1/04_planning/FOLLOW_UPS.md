# Procurement Planning — outstanding follow-ups

Items deliberately left open at the close of the **PLN-CHG-001 v1.2** rebuild
(Phases 0–12, closed 31 August 2026). Each is either an owner decision the
rebuild had no authority to make, a gap in a sibling module's own contract, or
a defect class with no live surface in MVP-1. Nothing here blocks the module's
acceptance contract; FU-01's §14.9 acceptance row (PLN-AC-046) was resolved
by retirement, not by the remediation this file originally described (see
below).

**Status:** re-annotated 5 September 2026 at the close of the SEED-001 v1.0 harmonized-fixture cutover: FU-01 is resolved by retirement (§1.1 removes the PE-KEBS fixture world outright rather than building the authoritative KEBS Budget Line/Strategic Objective this file previously called for). Earlier note at the close of the v1.12 correction cycle (FU-08..FU-11 added; FU-02 and FU-06 closed by v1.12). Earlier note from the cycle start: annotated 5 September 2026 at the start of the v1.12 correction cycle (`IMPLEMENTATION_TRACKER.md`): FU-02 and FU-06 are closed by that cycle (D11 adds `reference` to the Budget contract; DES-13 now has an artboard and is built); FU-01, FU-03, FU-04, FU-05, FU-07 are carried unchanged. Reservation-related wording in FU-05/FU-06 is moot under v1.12 §7.3 (Planning holds no reservation).

## Register

| ID | Item | Severity | Owner |
|---|---|---|---|
| FU-01 | **Resolved by retirement (SEED-001 §1.1, 5 Sep 2026).** §14.9 KEBS seed profiles were blocked on no authoritative KEBS Budget Line or Strategic Objective; the PE-KEBS fixture world is now deleted outright rather than completed — `seed_kebs_profiles` and its static-contract test are removed | Closed | — |
| FU-02 | Budget/Strategy published contracts expose no human business reference — screens show raw hash ids for Budget Lines | Medium | `kentender_budget` (and `kentender_strategy` for path-only labels) |
| FU-03 | The KENTENDER_MVP_V1 full-stack validator crashes upstream of the Planning checks on the retired `Strategy Programme` doctype | Medium | `kentender_strategy` / `kentender_core` seeds |
| FU-04 | Dormant references to retired Planning doctypes survive in tender-management and legacy seed families | Medium — latent crash-on-call, no live caller | `kentender_procurement` (tender-management), `kentender_core` legacy seeds |
| FU-05 | A successor's frozen governance snapshot cannot distinguish a carried-over item from one proposed for removal (no `item_state` in `_build_snapshot`) | Low — no UI trigger for removal exists in MVP-1 | `kentender_procurement` (Planning) + a design decision |
| FU-06 | `RemovePlanItemInSuccessor` / `CancelPlanUpdate` / `RetryPublication` have no UI trigger; PLN-DES-13 (Publication Result screen) deliberately not built | Low — service layer complete and tested | Design authority (next PLN revision) |
| FU-07 | The drawdown commands are System-Manager-gated pending a real Requisitions role vocabulary | Low — correct until the Requisitions module exists | The future Requisitions module's contract |
| FU-08 | PLN-CHG-001 v1.12 §14.5's illustrative milestone dates (23 May → 23 Jun evaluation) imply a 31-day evaluation period, above the governed 30-day ceiling of §4.9 / PLN-AC-114; the seed derives its baseline from the governed defaults PLN-DES-09 shows (1 May, 22 May, 21 Jun, 26 Jun, 28 Jun, 12 Jul, 31 Aug) | Low — a spec table to correct at the next PLN revision | Design authority (next PLN revision) |
| FU-10 | The §14.3 Strategy prerequisite (`STR-MOH-2023-001` with Objective “Strengthen interoperable national digital health services”) does not exist on the one-site model: Strategy’s v1.6 seed (STR tracker row STR-802) is still Planned and `kentender_mvp_v1_strategy.upsert_kentender_mvp_v1_strategy` returns a superseded marker | **High** — the Planning §14 seed fails loudly on it (§14.1), so `PLN-G07`'s live baseline and persona pass wait on it | `kentender_strategy` seeds (STR-802) |
| FU-11 | The §14.3 Budget prerequisite exists but its Line Versions are owned by the legacy unit `MOH-DIR-DHP`, while the shared register grants Grace/Peter on the site seed’s `Digital Health` unit; `list_eligible_budget_lines(source_org_unit=…)` therefore returns nothing for the department, and `kentender_core.seeds.kentender_mvp_v1.orchestrator.run_kentender_mvp_v1` (`make seed-kentender-mvp-v1`) fails upstream in its legacy org stage on the single-root rule | **High** — same effect as FU-10 | `kentender_core` seed orchestrator + `kentender_budget` seed (BUD §15.3 on the site-seed units) |
| FU-12 | Three acceptance rows are Partial after v1.12 Phase 8: PLN-AC-097 (county resident-tenderer advisory exists in `plan_readiness` and the editor control but no county-entity site fixture exercises it end to end), PLN-AC-101 (`item_status` exists; an optional Project Name on the plan header is not modelled — §4 defines no field for it), PLN-AC-110 (§7.5A's seven-return field-by-field verification is asserted only through the OCDS payload / Third Schedule tests, not as its own table-driven test) | Low | `kentender_procurement` (Planning) + design authority for the Project Name field |
| FU-09 | §14.2 names Peter Kimani's Digital Health assignment as split (ending 25 Nov 2026, successor from 1 Dec) with Julia acting 26–30 Nov; the shared KT-STD-001 §8.3 register seeded by `kentender_core.seeds.site_setup` holds Peter permanently and Julia acting 1 Oct–30 Nov, and the Planning seed verifies rather than re-grants the shared register (§14.2) | Low — a register alignment across NDS and Planning | `kentender_core` site seed + KT-STD-001 §8.3 |

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
- **FU-10/FU-11:** `bench --site <site> execute kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.verify_prerequisites` returns the resolved records instead of throwing; then `make seed-kentender-mvp-v1` completes and `npx playwright test tests/ui/smoke/planning/planning-release-evidence.spec.ts --workers=1` (the §14 persona pass) is green.
- **FU-07:** the Requisitions contract names its principal; the two gates
  check that role and `test_plan_requisition`'s masking test uses it.
