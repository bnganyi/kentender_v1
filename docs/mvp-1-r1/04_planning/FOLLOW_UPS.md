# Procurement Planning — outstanding follow-ups

Items deliberately left open at the close of the **PLN-CHG-001 v1.2** rebuild
(Phases 0–12, closed 31 August 2026). Each is either an owner decision the
rebuild had no authority to make, a gap in a sibling module's own contract, or
a defect class with no live surface in MVP-1. Nothing here blocks the module's
acceptance contract except FU-01, whose §14.9 acceptance row (PLN-AC-046) is
explicitly marked Open in the tracker.

**Status:** all open as of 31 August 2026.

## Register

| ID | Item | Severity | Owner |
|---|---|---|---|
| FU-01 | §14.9 KEBS seed profiles are blocked: no authoritative KEBS Budget Line or Strategic Objective exists for Planning to reference | **High** — PLN-AC-046 is Open until decided | Project Owner + `kentender_budget` / `kentender_strategy` seeds |
| FU-02 | Budget/Strategy published contracts expose no human business reference — screens show raw hash ids for Budget Lines | Medium | `kentender_budget` (and `kentender_strategy` for path-only labels) |
| FU-03 | The KENTENDER_MVP_V1 full-stack validator crashes upstream of the Planning checks on the retired `Strategy Programme` doctype | Medium | `kentender_strategy` / `kentender_core` seeds |
| FU-04 | Dormant references to retired Planning doctypes survive in tender-management and legacy seed families | Medium — latent crash-on-call, no live caller | `kentender_procurement` (tender-management), `kentender_core` legacy seeds |
| FU-05 | A successor's frozen governance snapshot cannot distinguish a carried-over item from one proposed for removal (no `item_state` in `_build_snapshot`) | Low — no UI trigger for removal exists in MVP-1 | `kentender_procurement` (Planning) + a design decision |
| FU-06 | `RemovePlanItemInSuccessor` / `CancelPlanUpdate` / `RetryPublication` have no UI trigger; PLN-DES-13 (Publication Result screen) deliberately not built | Low — service layer complete and tested | Design authority (next PLN revision) |
| FU-07 | The drawdown commands are System-Manager-gated pending a real Requisitions role vocabulary | Low — correct until the Requisitions module exists | The future Requisitions module's contract |

---

### FU-01 — §14.9 KEBS profiles blocked on missing authoritative fixtures

`seed_kebs_profiles` fails loudly by design: PE-KEBS exists (the
`kebs_foundation` seed creates PE/FY/OU/context only), but a funded,
submitted, accepted KEBS DPP — the prerequisite for forming
`PPI-KEBS-2026-ICT-001` — requires a KEBS Budget Line and a KEBS Strategic
Objective. §14.3 names only MOH fixtures, Budget's and Strategy's approved
seed contracts provide nothing for PE-KEBS, and §14.1 forbids Planning
inventing either. **Decision required:** extend the owning modules' seed
contracts with an authoritative KEBS Budget/Strategy graph, or descope
§14.9's Planning half (NDS's own §14.6 KEBS profile stopped at accepted
Needs for the same underlying reason). `PLN-AC-046` stays Open until then.

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

- **FU-01:** `bench --site <site> execute kentender_procurement.procurement_planning.seeds.kentender_mvp_v1.seed_kebs_profiles`
  stops throwing and builds `PPI-KEBS-2026-ICT-001` twice (Need-origin and
  direct) with equivalent lineage; `test_planning_seed`'s KEBS test flips
  from "fails loudly" to a build assertion; PLN-AC-046 → Done.
- **FU-02:** the owning contract returns a `reference` field; DES-02/03/09
  screens display it; re-capture the affected evidence screenshots.
- **FU-03:** `bench --site <site> execute kentender_core.seeds.kentender_mvp_v1.orchestrator.validate_kentender_mvp_v1`
  completes and its report contains the `planning.v12.*` checks, all passing.
- **FU-04:** repo-wide grep for the nine retired doctype names returns only
  history/docs; the tender-management suites still pass.
- **FU-05/FU-06:** a design artboard exists first; then the snapshot/UI work
  cites it.
- **FU-07:** the Requisitions contract names its principal; the two gates
  check that role and `test_plan_requisition`'s masking test uses it.
