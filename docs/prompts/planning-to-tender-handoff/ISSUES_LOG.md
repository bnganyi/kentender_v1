# Planning → Tender handoff — ISSUES_LOG

**Canonical log** for integration workstream issues **`STD-INT-*`**, **`STD-INT-SEED-*`**, and cross-posts from implementation tracks in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md).

---

## Design sign-off — 2026-05-03

| ID | Type | Summary | Status |
|----|------|---------|--------|
| STD-INT-SIGNOFF-001 | meta | Section A (A1–A5) design artefacts reviewed against doc acceptance criteria and exit conditions; **no specification-level deferrals**; implementation debt remains in tracker §B–§D. | Closed |

---

## Reserved — Doc 3 seed refactor (open when implementing)

Use these ids when work starts; align with [doc 3 §30](3.%20works_seed_scenario_refactor_specification.md).

| ID | Summary |
|----|---------|
| STD-INT-SEED-001 | Integrated Works seed must originate from Procurement Package, not standalone tender |
| STD-INT-SEED-002 | Planning Template to STD Template mapping must be explicit |
| STD-INT-SEED-003 | **B1 done (2026-05-03):** DocType has `procurement_plan` / `procurement_package` / `procurement_template` + lineage validate. **Remaining:** populate via **B3** release + **C** seed; close when integrated seed asserts linkage. |
| STD-INT-SEED-004 | Representative BoQ must align with package/lot structure |
| STD-INT-SEED-005 | Officer completion values must not be confused with upstream planning values |

---

## How to log

1. Add a row under a dated section or a component section (Handoff / Seed / Hardening).
2. Use **`STD-INT-NNN`** for new integration issues (next free number after scanning this file).
3. Reference the id from **Notes** in `IMPLEMENTATION_TRACKER.md`.
