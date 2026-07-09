# BE-00 — Repository Audit Report

**Date:** 2026-07-09  
**Site:** `kentender.midas.com`  
**Tracker:** `BE_IMPLEMENTATION_TRACKER.md`  
**Status:** Complete — scaffold + gate tests green

## Goal

Confirm Frappe conventions, propose exact `std_engine` file locations, identify risks/blockers, and land a minimal importable module scaffold **before** BE-01 DocTypes or import code.

## Stack summary

| Layer | Choice |
|---|---|
| Framework | Frappe / ERPNext bench |
| App | `kentender_procurement` (`kentender_procurement.std_engine`) |
| Database | MariaDB via Frappe DocTypes (`bench migrate`) |
| API transport | `@frappe.whitelist()` → `/api/method/kentender_procurement.std_engine.api.<fn>` |
| Desk UI | Frappe Pages + iframe static HTML + `std_prod_*_page.js` |
| Unit/integration tests | `bench --site kentender.midas.com run-tests --module …` |
| UI smoke | Playwright under `apps/kentender_v1/tests/ui/smoke/std-prod-impl/` |
| Seed data | `apps/kentender_v1/docs/std-prod-impl/data/` |

No Node/TypeScript backend — Cursor pack `/src/modules/std-engine/` maps to Python under `std_engine/`.

## Existing module patterns (reference)

### Subdomain packages inside `kentender_procurement`

| Module | Path | Frappe `modules.txt` label | Pattern |
|---|---|---|---|
| Demand Intake | `demand_intake/` | `Demand Intake` | `api/`, `doctype/`, `services/`, `seeds/`, `tests/` |
| Procurement Planning | `procurement_planning/` | `Procurement Planning` | Same + `permissions/` |
| Tender Management | `tender_management/` | `Kentender Procurement` (default) | Large TM2 surface; **not** STD Engine owner |

DocTypes set `"module": "<modules.txt label>"` (e.g. `"Demand Intake"`).

### API pattern

- Whitelist in `api/*.py`, delegate to `services/*.py`
- Example: `tender_management/api/tm2_workbench.py` → `services/tm2_workbench_*.py`
- Desk calls via `frappe.call({ method: "kentender_procurement.<module>.api.<file>.<fn>" })`

### Bench execute pattern

- Seeds expose `run()` entrypoints
- Example: `bench --site kentender.midas.com execute kentender_procurement.demand_intake.seeds.seed_dia_basic.run`

STD import will follow: `kentender_procurement.std_engine.import.dry_run.run` / `commit.run`.

### Test pattern

- `UnitTestCase` for file/hook/constant gates (no DB)
- `IntegrationTestCase` for site DocType/Page existence
- Module path: `<package>/tests/test_<ticket>_<subject>.py`
- STD prod UI tests live in `tender_management/tests/test_std_prod_*` (layout guards + desk wiring) — **remain there**; new backend tests go under `std_engine/tests/`

## Proposed `std_engine` layout (approved)

```text
apps/kentender_procurement/kentender_procurement/std_engine/
  __init__.py              MODULE_NAME
  README.md                boundary doc
  constants.py             lifecycle enum, M1 commit state, UI mode
  paths.py                 seed zip + official PDF resolution
  api/
    __init__.py
    read.py                BE-06+ read whitelists
    import_api.py          BE-04a dry-run / commit / import-runs
  package_import/
    __init__.py
    package_reader.py      BE-02 ✅
    manifest_validator.py
    checksum_verifier.py
    package_contract.py
    dry_run.py               BE-03 (+ bench execute run)
    commit.py                BE-04 (+ bench execute run)
  validation/
    __init__.py
    validators/              BE-05
  audit/
    __init__.py
    event_service.py         BE-04+
  services/
    __init__.py
    envelope.py              packageContext + uiMode response builder
  doctype/                   BE-01
    std_family/
    std_version/
    …
  tests/
    test_be_00_module_scaffold.py   ✅
    test_be_01_*.py                 (next)
```

**Import path:** `kentender_procurement.std_engine`  
**Filesystem:** `apps/kentender_procurement/kentender_procurement/std_engine/`

## DocType naming (BE-01 preview)

Follow existing KenTender style — Title Case DocType names, snake_case folders:

| Logical entity | DocType name | Autoname candidate |
|---|---|---|
| std_family | `STD Family` | `field:family_code` |
| std_version | `STD Version` | `field:package_id` |
| std_source_document | `STD Source Document` | hash or business key |
| std_import_run | `STD Import Run` | `format:STD-IMP-{#####}` |

All DocTypes: `"module": "STD Engine"`.

## API naming (BE-06+ preview)

| External contract (tracker) | Frappe whitelist |
|---|---|
| `GET /std-engine/import-runs/:id` | `import_api.get_import_run(import_run_id)` |
| `POST /std-engine/import/dry-run` | `import_api.dry_run(zip_path, pdf_path)` |
| `POST /std-engine/import/commit` | `import_api.commit(...)` |
| `get_std_families` | `read.get_std_families()` |

HTTP routes in tracker are **logical**; Frappe transport is `/api/method/...` until custom route handlers are added.

## UI integration (existing — do not relocate)

| Concern | Location |
|---|---|
| Static screens | `public/std_prod_impl/*.html` |
| Desk pages | `page/std_library`, `std_family_detail`, `std_version_detail` |
| Iframe wiring | `public/js/std_prod_std_*_page.js` |
| Future API calls | Add `frappe.call` in page JS → `std_engine.api.read` |

Screens 04–22 need new Frappe Pages in later wiring tickets (vertical slice notes "TBD").

## Legacy / collision risks

| Risk | Mitigation |
|---|---|
| `tender_management/services/std_template_loader.py` retired stub | Do not extend; `std_engine` is canonical |
| UI mock `KE-PPRA-IT-2024-04` in static HTML | JS hydration from API only (tracker rule) |
| v0.2 `activation_allowed: false` | Commit as DRAFT; blockers → validation findings |
| `import/` is Python keyword | Package name `import` is valid; use `from kentender_procurement.std_engine import import as std_import` if needed, or submodule imports via `importlib` |
| NSSF fixtures inside zip | Skip by policy; never master STD |
| No second package for screen 21 | Single-version stub API |

## Seed artifact verification

| File | Present | Notes |
|---|---|---|
| `KE-PPRA-IT-2022-04_Seed_Package_v0_2.zip` | ✅ | 76 nested JSON files |
| `DOC 10. STD FOR PROCUREMENT OF INFORMATION TECHNOLOGY.pdf` | ✅ | Must register on commit |
| `NSSF SPS RFP ERP 2026.pdf` | ✅ | Calibration only — do not import |
| Skeleton zip | ❌ not in `data/` | Not needed for M1 |

## BE-00 deliverables

| Deliverable | Path | Evidence |
|---|---|---|
| Audit report | `docs/std-engine/BE-00_REPO_AUDIT.md` | This file |
| Module scaffold | `std_engine/` | Directory tree |
| Frappe module registration | `modules.txt` + `MODULE_NAME` | Gate test |
| M1 constants | `std_engine/constants.py` | Gate test |
| Seed path resolver | `std_engine/paths.py` | Gate test (files exist on disk) |
| Scaffold gate tests | `std_engine/tests/test_be_00_module_scaffold.py` | 9/9 unit tests |

## Test evidence

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.std_engine.tests.test_be_00_module_scaffold
```

Expected: **9 tests OK**.

## Next ticket

**BE-01** — Core DocTypes with lifecycle enum, `activation_allowed`, `ui_mode`, package/hash fields, and `STD Import Run`.
