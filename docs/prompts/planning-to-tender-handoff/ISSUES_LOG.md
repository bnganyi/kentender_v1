# Planning → Tender handoff — ISSUES_LOG

**Canonical log** for integration workstream issues **`STD-INT-*`**, **`STD-INT-SEED-*`**, and cross-posts from implementation tracks in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md).

---

## Design sign-off — 2026-05-03

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-INT-SIGNOFF-001 | meta | Section A (A1–A5) design artefacts reviewed against doc acceptance criteria and exit conditions; **no specification-level deferrals**; implementation debt remains in tracker §B–§D. | Closed |

---

## Integrated WORKS seed — doc 3 §30 (`STD-INT-SEED-*`) — disposition 2026-05-03

Canonical spec: [doc 3 §30](3.%20works_seed_scenario_refactor_specification.md). Implementation evidence: [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) §C1–C6, [`procurement_planning/seeds/README.md`](../../../kentender_procurement/kentender_procurement/procurement_planning/seeds/README.md).

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-INT-SEED-001 | seed | Integrated `STDINT-WORKS-S01` chain ends with `workflow.release_package_to_tender` → B3 `release_procurement_package_to_tender` hook; no standalone `Procurement Tender` insert in seed. | **Closed** |
| STD-INT-SEED-002 | seed | `Procurement Template.default_std_template` set to `KE-PPRA-WORKS-BLDG-2022-04-POC` after loader (`seed_works_stdint_s01` §26 / C2); explicit Link + validate (B2). | **Closed** |
| STD-INT-SEED-003 | handoff | Persistent `procurement_plan` / `procurement_package` / `procurement_template` (and audit hash/snapshot) populated on tender at release (B1/B3/B8); C3 + `works_stdint_s01_verification.gather_doc3_section_28_checks` assert linkage. | **Closed** |
| STD-INT-SEED-004 | hardening | Full BoQ/lot alignment with **package lines** and bill structure deferred to doc 4/5 (WH). **Partial in v1:** C6 §29 smoke uses verification `Tender Lot` rows + STD `generate_sample_boq` (9 rows) + validation/preview only — not procurement-package-derived BoQ. | **Open** |
| STD-INT-SEED-005 | seed | Labelled officer merge: `SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_LABEL` / merge version keys; README §20; neutral seed copy (not `load_sample_tender` / not planning authority). | **Closed** |

---

## How to log

1. Add a row under a dated section or a component section (Handoff / Seed / Hardening).
2. Use **`STD-INT-NNN`** for new integration issues (next free number after scanning this file).
3. Reference the id from **Notes** in `IMPLEMENTATION_TRACKER.md`.
