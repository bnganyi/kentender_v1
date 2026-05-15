# G0-003 — Existing seed inventory and WORKS conflict matrix

**Parent gate:** [G0-003](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md)  
**Atomic tickets:** LV-G0-003-01, LV-G0-003-02  
**Master registry:** [2. procurement_lifecycle_works_master_seed_data_specification.md](./2.%20procurement_lifecycle_works_master_seed_data_specification.md) **§4**  
**Seed entrypoint index:** [G0-001_repository_inventory.md](./G0-001_repository_inventory.md) **LV-G0-001-04**  
**Evidence command (bench root):** `rg` over `apps/kentender_v1/**/seeds/**/*.py` and `apps/kentender_v1/docs/audit/**/seeds/**/*.py` for literals below (run 2026-05-15).

---

## Evidence summary (§3.2 template)

```text
Implementation Evidence:
- LV-G0-003-01: conflict / alignment matrix (this file) + cited Python modules and JSON fixtures.
- LV-G0-003-02: non-master seed policy subsection.
- Search: ripgrep across **/seeds/**/*.py under apps/kentender_v1 (including docs/audit/.../seeds).

Test Evidence:
- N/A for G0-003 (documentation-only gate).

Result:
- Matrix complete for §4.1; §4.2/§4.3 called out where literals absent.
- G0-003 and LV-G0-003-01–02 **Accepted** in [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) §5 / §18.1.

Review Notes:
- Decision: **Accepted** (seed inventory + WORKS conflict matrix gate).
```

---

## LV-G0-003-01 — Seed conflict / alignment matrix (§4.1 business codes)

**Legend — Match type:** **Exact** = same string in seed/fixture code; **Alias** = documented alternate / coexistence pattern; **Partial** = overlaps story anchor but different string or version; **None** = no literal found under `**/seeds/**/*.py` (fixtures or R2 may still introduce).

### §4.1 Core business codes

| Master code (spec §4.1) | Match type | Repo location(s) | Risk | Recommended disposition |
|-------------------------|------------|-------------------|------|---------------------------|
| JRN-MOH-2026-001 | None | — | Low until R4 journey loader lands | R2: reserve when creating `Procurement Journey` seed rows. |
| PE-MOH | Partial | Spec uses `PE-MOH`; core/procurement seeds use procuring entity code **`MOH`** (`kentender_core/.../constants.py` `ENTITY_MOH`; TM2 seeds set `procuring_entity_code = "MOH"`). | Master queries keyed on `PE-MOH` may miss rows | R2: map `PE-MOH` ↔ `MOH` in master loader **or** amend spec to `MOH` with explicit migration note. |
| STRAT-MOH-2026 | None | Core strategy seeds use **plan titles** (`PLAN_BASIC_NAME` etc.), not this code string in `**/seeds/**/*.py`. | Story drift vs named master plan | R2: emit `strategic_plan` / programme codes per §8 or align titles + codes. |
| PROG-MOH-INFRA | None | (same as above) | Same | Same |
| OBJ-MOH-HOSP-RENOV | None | No literal in seeds scanned | Same | R2 |
| TGT-MOH-HOSP-RENOV-2026 | None | No literal in seeds scanned | Same | R2 |
| BUDGET-MOH-2026 | None | Core budget seeds use names `FY2026 Budget` (`_budget_seed_common.py`), not `BUDGET-MOH-2026`. | Same | R2 |
| BUD-MOH-INFRA-2026-001 | Partial | DIA/planning stack uses **`BL-MOH-2026-001`** as budget line business code (`kentender_core/.../seed_budget_line_dia.py`, `seed_works_stdint_s01.py` `BL_CODE`, `dia_seed_common.py`). **Not** the spec string. | Parallel budget-line namespace; master journey join wrong if only spec code queried | R2: rename BL-* → `BUD-MOH-INFRA-2026-001` **or** treat BL-* as legacy and migrate; document in R2-013 if UAT has both. |
| DEM-MOH-2026-001 | Alias | `seed_works_stdint_s01.py` uses **`DEM-MOH-WORKS-2026-001`** / `DEM-MOH-WORKS-2026-002` (intentional peer). DIA smoke uses **`DIA-MOH-2026-*`** demand_id space, not `DEM-MOH-2026-001`. | No collision on exact string; master DEM code unused in current seeds | R2: master loader creates `DEM-MOH-2026-001`; keep WORKS-S01 / DIA as **non-master** (LV-G0-003-02). |
| DEMITEM-MOH-2026-001-001 | None | — | Low | R2 |
| DEMAPPROVAL-MOH-2026-001 | None | — | Low | R2 |
| PLAN-MOH-2026 | Alias | `seed_works_stdint_s01.py`: **`PLAN-MOH-2026-WORKS-S01`** “equivalent” to §12 `PLAN-MOH-2026`. F1/PP3 use **`PP-MOH-2026`** (`seed_procurement_planning_f1.py`, `seed_planning_pp3_slice.py`). | Multiple plan code families on one site | Master: single canonical `PLAN-MOH-2026`; mark F1/PP3/S01 as **non-master** prefixes. |
| PKG-MOH-2026-001 | Exact | `seed_std_inst_1400.py`, `works_completion_moh_fixture.py`, `seed_works_stdint_s01.py`, `seed_pub_moh_1100.py`, `seed_derived_moh_1200.py`, `seed_procurement_planning_f1.py`, `seed_planning_pp3_slice.py`; duplicate definitions in `docs/audit/planning_tender_handoff_2026-05-03/seeds/`. | **High:** many seeds assume same package anchor; order-of-run and idempotency conflicts | Enforce single owner in **R2 master loader**; other seeds must skip or use `is_master_seed` / non-master policy; see coexistence comments in `works_completion_moh_fixture.py` and `seed_pub_moh_1100.py`. |
| PKGLINE-MOH-2026-001-001 | Partial | `seed_works_stdint_s01.py` uses **`PKGL-MOH-2026-001-01`** / `-02` (pattern differs from spec `PKGLINE-…`). | Join key mismatch vs spec | Align naming in R2 **or** amend spec to PKGL-* pattern. |
| STD-WORKS | None | No literal in seeds scanned (STDINST-1400 resolves template via Frappe, not this string in module constants) | Loader must pin template | R2 |
| STDTV-WORKS-BUILDING-CIVIL-APR2022 | None | No literal in scanned seed constants | Same | R2 |
| WORKS-PROFILE-BUILDING-CIVIL | Partial | `seed_std_inst_1400.py` / `works_completion_moh_fixture.py`: **`WORKS-PROFILE-BUILDING-CIVIL-REV-APR-2022`** (suffix `REV-APR-2022` vs spec short code). | **String drift** vs §4.1 | Resolve in **R2 loader** or **spec amendment**; do not silently equate. |
| STDINST-TND-MOH-2026-001 | Exact / Partial | **Exact** in `seed_derived_moh_1200.py` `INSTANCE_CODE` and fixtures `kentender_procurement/.../fixtures/tm2_seed_works_open_tender.json` (and audit copy). `seed_pub_moh_1100.py` uses **pattern** `STDINST-TND-MOH-PUB1100-{tag}` (alias namespace). | Multiple STD instance codes targeting same tender | Publication seed uses distinct tag; document in runbooks. |
| TND-MOH-2026-001 | Exact | Same modules as `PKG-MOH-2026-001` row + fixtures. | High (shared tender anchor) | Same as package: single master owner; CI suffix option in `works_completion_moh_fixture.py`. |
| TSB-TND-MOH-2026-001 | None | No literal in seeds scanned | R2 binding step | R2 |
| GB-TND-MOH-2026-001-V2 (and DSM/DOM/DEM/DCM **-V2**) | Partial | **Fixtures** `tm2_seed_works_open_tender.json` use **-V2** (matches spec). `seed_derived_moh_1200.py` uses **-V1** outputs. | Version skew between fixture JSON and Python seed | Tests must pick one canonical chain; R2 aligns outputs to §4.1. |
| PUBSNAP-TND-MOH-2026-001-V2 | Partial | Fixture exact; seeds use `SNAP-PUB-TND-MOH-2026-001-V1` in `seed_derived_moh_1200.py` | Same | Same |
| ADD-TND-MOH-2026-001-01 | Partial | Fixture exact; not seen in scanned `**/seeds/**/*.py` literals | Low in seeds | R2 / fixtures |
| PUB-TND-MOH-2026-001-001 | None | — | R2 publication record | R2 |
| ORR-TND-MOH-2026-001 | None | — | R2 opening readiness | R2 |
| CLS-TND-MOH-2026-001 | None | — | R2 closing | R2 |

**Fixture evidence (not `bench execute`, still repo):**

- [`kentender_procurement/kentender_procurement/tender_management/fixtures/tm2_seed_works_open_tender.json`](../../../kentender_procurement/kentender_procurement/tender_management/fixtures/tm2_seed_works_open_tender.json) — aligns several §4.1 strings to **-V2** (matches spec closer than DERIVED-1200 **-V1** constants).

### §4.2 Handoff codes

| Master code (spec §4.2) | Match type | Repo seeds |
|-------------------------|------------|------------|
| STRATREF-MOH-2026-001 … OPENREADY-TND-MOH-2026-001 | **None** | No literals in `apps/kentender_v1/**/seeds/**/*.py`. Handoff cards are **R2+** / journey layer per tracker. |

### §4.3 User codes

| Master user code (spec §4.3) | Match type | Repo seeds |
|------------------------------|------------|------------|
| USER-* / SUPUSER-* | **None** as codes | Seeds use **email** identities (e.g. `*@moh.test` in `kentender_core/.../constants.py`). | R2: map table spec §4.3 → actual `User` names/emails in master seed loader. |

---

## LV-G0-003-02 — Non-master seeds policy

1. **`is_master_seed`** — WORKS master spec already marks master rows with `is_master_seed: true` in narrative tables. **R2** loaders should set this flag on DocTypes where the field exists, and journey/evidence queries should **filter** `is_master_seed = 1` for “District Hospital Renovation Works” canonical demos.

2. **Legacy seeds without the flag** — Treat as **non-master** if any of:
   - code uses a **documented alias** (`PLAN-MOH-2026-WORKS-S01`, `DEM-MOH-WORKS-*`, `PP-MOH-2026`, `DIA-MOH-*`, `PKGL-MOH-*`, `STDINST-TND-MOH-PUB1100-*`, `REL-PKG-MOH-PUB1100-*`, …),
   - seed docstring states coexistence / F1 / PP3 / smoke purpose,
   - path under `docs/audit/.../seeds/` (audit-only; see G0-001).

3. **Query exclusion** — Procurement lifecycle **journey APIs** (rectification pack) must not aggregate non-master rows when answering “master journey” unless explicitly in **debug** or **UAT collision** mode (**LV-R2-013-01**).

4. **Reset scope** — Master reset (`load_procurement_lifecycle_works_master`, R2) must only delete/recreate rows flagged master or allowlisted codes from §4.1; **must not** assume `reset_core_seed` / `seed_dia_empty` cleared WORKS master rows unless product defines a combined wipe (out of scope for G0-003).

5. **Audit-only entrypoints** — Do not schedule `docs/audit/planning_tender_handoff_2026-05-03/seeds/*.py` in production pipelines; they duplicate F1/PP3 constants and **`PKG-MOH-2026-001`** ([G0-001](./G0-001_repository_inventory.md) LV-G0-001-04).

---

## Appendix A — LV-G0-001-04 entrypoints vs WORKS §4 touch

| Module path (from G0-001 §LV-G0-001-04) | Touches WORKS §4 codes? | Notes |
|----------------------------------------|-------------------------|--------|
| `kentender_core.seeds.seed_core_minimal` | Partial | `MOH` entity only |
| `kentender_core.seeds.dev_full_reseed` | Partial | Orchestrates core |
| `kentender_core.seeds.reset_core_seed` | Partial | Wipes MOH/MOE entities |
| `kentender_core.seeds.seed_strategy_*` / `reset_strategy_seed` | None / Partial | Titles not §4 strings |
| `kentender_core.seeds.seed_budget_*` | Partial | FY budget names |
| `kentender_core.seeds.seed_budget_line_dia` | **Partial** | **`BL-MOH-*`** vs `BUD-MOH-INFRA-2026-001` |
| `kentender_procurement.demand_intake.seeds.seed_dia_*` | Partial | **`DIA-MOH-*`**, `BL-MOH` prereqs |
| `…seed_dia_planning_f1_prerequisites` | Partial | DIA + BL-MOH |
| `…seed_procurement_planning_f1` | **Partial** | **`PKG-MOH-2026-001`**, `PP-MOH-2026` |
| `…seed_planning_pp3_slice` | **Partial** | Same package code |
| `…seed_works_stdint_s01` | **Partial** | **`PKG-MOH-2026-001`**, alias plan/demand codes, BL-MOH |
| `…validate_planning_seed_dependencies` | Partial | Checks DIA + BL codes |
| `kentender_procurement.tender_management.seeds.seed_std_inst_1400` | **Partial** | **Exact** PKG/TND; profile **drift** |
| `…tender_publication.seeds.seed_pub_moh_1100` | **Partial** | PKG + tagged STD instance |
| `…derived_models.seeds.seed_derived_moh_1200` | **Partial** | TND + **V1** output codes vs spec **V2** |
| `…works_completion.seeds.works_completion_moh_fixture` | **Partial** | PKG/TND + profile drift + coexistence rules |
| `docs/audit/.../seeds/*` | **Partial** | Duplicates planning/DIA constants; audit-only |

---

## Tracker cross-walk

| Ticket | Section |
|--------|---------|
| LV-G0-003-01 | LV-G0-003-01 |
| LV-G0-003-02 | LV-G0-003-02 |
