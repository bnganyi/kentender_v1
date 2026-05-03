# Procurement planning seeds

## WORKS integrated scenario (`seed_works_stdint_s01`)

### Doc 3 §18.1 — Preferred path (canonical in this repo)

[`seed_works_stdint_s01.run`](seed_works_stdint_s01.py) ends by driving the procurement plan and package through
[`workflow.release_package_to_tender`](../api/workflow.py). That calls
[`deliver_procurement_package_release`](../services/tendering_handoff.py), which runs the
`release_procurement_package_to_tender` hook implemented in
[`release_procurement_package_to_tender.py`](../../tender_management/services/release_procurement_package_to_tender.py)
(tracker **B3**). The package reaches **Released to Tender**; `Procurement Tender` is created with plan/package/STD
links and handoff `configuration_json` (tracker **C3**).

### Doc 3 §20 — Sample officer completion (tracker **C5**)

After release, `seed_works_stdint_s01.run` may merge **labelled** sample deadline / site visit / pre-tender meeting /
security / JV / qualification / dayworks and provisional sums values into the tender’s `configuration_json`, plus
`SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_LABEL` stating this is **not** Planning authority data. The step is idempotent
(`SEED.STDINT_WORKS_S01.SAMPLE_OFFICER_APPLIED`). See `_apply_works_s01_sample_officer_completion` in
[`seed_works_stdint_s01.py`](seed_works_stdint_s01.py).

### Doc 3 §28–29 — Verification + smoke (tracker **C6**)

[`works_stdint_s01_verification.py`](works_stdint_s01_verification.py) implements **§28** structural checks (budget line
strategy link, demands, approved plan, template→STD, package lines vs header value, release status, tender lineage,
hashes) and **§29** tender-stage smoke: two `Tender Lot` rows for BoQ lot verification, `validate_tender_configuration`
→ `generate_sample_boq` (9 rows) → re-validate → `generate_required_forms` → `generate_tender_pack_preview` (officer
path: **8** forms, see `officer_path_required_forms_count` in smoke output), then **`load_sample_tender`** so the
tender matches primary `sample_tender.json` (Step 16), re-validate, regenerate **15** required forms + preview, then
**doc 5 §25 / WH-013** — `run_works_tender_stage_hardening` (orchestration, validation persistence, §23 snapshot + hash).
Integrated seed must finish with **no Critical** findings (`critical_count == 0`); **Warning** on overall hardening
status is expected when derived-model placeholders block future publication. See planning handoff doc 5 §25.

`seed_works_stdint_s01.run()` returns `section_28_verification` and `section_29_smoke` when a tender exists after
release. **Forms count:** doc §28 lists **15** required forms for the **full** primary `sample_tender.json` identity
(STD-WORKS-POC Step 16). The first §29 segment still avoids `load_sample_tender` until after officer-merge preview (B7);
WH-013 then loads the primary sample **only** to satisfy doc 5 §25 hardening without weakening §18 Critical rules.

### Doc 3 §30 — Issue log (`STD-INT-SEED-*`, tracker **C7**)

Disposition for **`STD-INT-SEED-001` … `005`** (closed vs open, including why **`004`** remains open until doc 4/5 BoQ
hardening) is recorded in the workstream
[`ISSUES_LOG.md`](../../../../docs/prompts/planning-to-tender-handoff/ISSUES_LOG.md).

### Doc 3 §18.2 — Transitional path (not used here)

Spec §18.2 allows temporarily inserting a tender **without** the release service when the service does not exist.

**This bench does not implement that shortcut:** B3 and C3 are in place. Do **not** add a silent
`Procurement Tender` insert path in this seed.

Forks that remove the service must re-introduce §18.2 only with an explicit seed flag, issue-log reference, and a
smoke path to migrate back to the service-driven release.

### Related code

- Hook registration: `kentender_procurement/hooks.py` (`release_procurement_package_to_tender`).
- Planning-to-tender handoff delivery: [`tendering_handoff.py`](../services/tendering_handoff.py).
