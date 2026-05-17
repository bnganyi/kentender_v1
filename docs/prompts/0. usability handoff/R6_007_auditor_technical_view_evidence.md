<!--
  Evidence for Rectification Tracker §11 — R6-007 / LV-R6-007-01
-->
# Goal

**Auditors and privileged desk users** must be able to open **full STD technical evidence** (Bundle / DSM / DOM / DEM / DCM output references) via the **expandable technical drawer** on business readiness — matching pack **§12.6** (*“…auditor can still open full STD technical evidence”*) and **R6-003** (`can_view_technical_output_codes` + collapsed UI).

# What was verified

| Layer | Check |
|-------|--------|
| **Seed** | **`auditor@moh.test`** is created by **`seed_core_minimal`** (same password as other seed users). |
| **Permissions** | **TM2 Tender** DocType includes **Auditor** role with **read** (and export/print/report for audit viewing) so auditors can load the Desk form used by this test. |
| **API** | **`auditor@moh.test`** session: `read_business_readiness_summary` → **`can_view_technical_output_codes: true`**. **Administrator** remains **true** (regression). |
| **UI (Auditor)** | On **`/app/tm2-tender/TND-MOH-2026-001`**, the readiness card is **not** the restricted message (`plc-br-technical-restricted` absent); user expands **“Technical output codes (advanced)”**, body becomes visible; either **`.plc-technical-output-code`** lines appear or **`plc-br-no-tech`** when no codes exist yet. |

# Evidence submitted (automated)

- **Site prep (after pulling this change):** `bench --site kentender.midas.com migrate` (syncs **TM2 Tender** permissions), then `bench --site kentender.midas.com execute kentender_core.seeds.seed_core_minimal.run` (creates **auditor@moh.test** if missing).
- Python: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_lifecycle.tests.test_r6_007_auditor_technical_readiness_access`
- Playwright (from `apps/kentender_v1`): `npx playwright test tests/ui/smoke/procurement/auditor_technical_drawer_r6_007.spec.ts --workers=1` — **PLC-R6-007-01**

# Related references

- **R6-003** — Administrator workbench technical drawer (`tm2_business_readiness_technical_drawer_r6_003.spec.ts`).
- **`readiness_api._can_view_technical_output_codes_for_session`** — **Auditor** in `internal_clearing`.
