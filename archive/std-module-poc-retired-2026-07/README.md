# STD Module POC — Archived (July 2026)

The entire POC-era STD stack (Desk UI, APIs, governance, instance runtime, seeds, tests, docs, React `std-engine`) has been **retired from active use** and preserved here for reference while a production-grade **STD Library Management** module is designed and built.

## Why archived

- Multiple incomplete POC layers (mockup-faithful Desk UI, library shell, configurator, governance, tender instance runtime, WORKS package loader, React `std-engine`) were blocking a clean production rebuild.
- Database rows on `kentender.midas.com` are **preserved** (no DocType deletion patches). Only code and active wiring were retired.

## How to browse

- **`ARCHIVE_MANIFEST.md`** — searchable list of every archived file with original path and bucket.
- **`SNAPSHOT_COMMIT.txt`** — git SHA tagged as `archive/std-module-poc-2026-07` (pre-retirement checkout).
- Mirror layout:
  - `kentender_procurement/` — moved paths from the procurement app
  - `kentender_v1/` — tests, frontend, docs
  - `.cursor/rules/` — STD-specific Cursor rules

## Active replacement

Desk routes that previously opened STD surfaces now redirect to **`std-module-retired`** (Frappe Page) with a static retirement notice.

Site flags (document in site config / README):

- `std_config_ui_v2_enabled: 0`
- `std_module_retired: 1`

## Expected breakage (until production module ships)

| Integration | Impact | Restore from |
|-------------|--------|--------------|
| **TM2 workbench** STD readiness / instance tabs | Tabs show retired stub or empty state | `kentender_procurement/.../tm2_std_adapter.py`, `std_instance/` |
| **Planning→tender handoff** | `KE-PPRA-WORKS-BLDG-2022-04-POC` resolution disabled | `planning_tender_handoff_xmv.py`, `std_template_handoff_resolution.py` |
| **Works completion APIs** | Endpoints archived | `tender_management/api/works_completion.py` |
| **PP2 / master seeds** | WORKS STD seed steps no-op | `seeds/works_master_std_seed.py` |
| **Procurement lifecycle** STD readiness handoff | Stub returns unavailable | `procurement_lifecycle/std_readiness_handoff.py` |

## Restore notes

1. Check out tag: `git checkout archive/std-module-poc-2026-07`
2. Or `git mv` paths back from this tree to their original locations (see manifest).
3. Re-enable hooks in `kentender_procurement/hooks.py`, workspace links, and CI gates.
4. Run `bench --site kentender.midas.com migrate` and `clear-cache`.
