# IT STD Wizard — Archived (July 2026)

The IT Tender Configuration Wizard (v1 iframe stack and v2 native migration) has been **retired from active use** and preserved here for reference while a clean rebuild is designed.

## Why archived

- v1/v2 implementation accumulated architectural debt (iframe engine, partial native migration, visual fidelity gaps).
- TM2 and STD Engine remain active; the wizard configuration layer is being restarted from scratch.
- Database rows on `kentender.midas.com` are **purged** via `retire_it_std_wizard_cleanup` migrate patch.

## How to browse

- **`ARCHIVE_MANIFEST.md`** — searchable list of every archived file with original path.
- **`SNAPSHOT_COMMIT.txt`** — git SHA at pre-removal checkout.
- Mirror layout:
  - `kentender_procurement/` — Python module, Desk pages, public assets, patches
  - `kentender_v1/` — Playwright tests, Makefile gates, CI workflow
  - `docs/std-prod-impl/` — IT-STD-Wizard v1/v2/v3 packs
  - `.cursor/rules/` — wizard-specific Cursor rules

## Active replacement

Desk routes that previously opened IT wizard surfaces redirect to **`it-std-wizard-retired`** (Frappe Page) with a static retirement notice.

## Expected breakage (until new wizard ships)

| Integration | Impact | Restore from |
|-------------|--------|--------------|
| **TM2 workbench** STD binding / publication tabs | Show retired/unavailable state | `tender_management_v2_workbench_page.js`, TM2 binding services |
| **Procurement sidebar** IT Tender Configurations | Removed | `workspace_sidebar/procurement.json` |
| **Publication derived outputs** (DSM/DOM/DEM) | Unavailable | wizard `it_tender_wizard/services/` |
| **Master WORKS seed** STD instance assertion | Removed or STD Engine only | `test_r2_009_works_master_tender_seed.py` |

## What stays active (not in this archive)

- **`std_engine/`** — STD Library Management (KE-PPRA-IT package import, governance, render)
- **`docs/std-prod-impl/cursor/`** — STD Engine production rules
- **`docs/std-prod-impl/data/KE-PPRA-IT-*`** — canonical IT STD seed packages

## Restore notes

1. Check out commit in `SNAPSHOT_COMMIT.txt` or browse this tree.
2. `git mv` paths back from manifest to original locations.
3. Re-enable hooks in `kentender_procurement/hooks.py`, workspace links, patches, and CI gates.
4. Run `bench --site kentender.midas.com migrate` and `clear-cache`.

When rebuilding, treat v1 iframe and v2 partial native screens as **reference only** — start from v3 control pack + STD Engine bind APIs.
