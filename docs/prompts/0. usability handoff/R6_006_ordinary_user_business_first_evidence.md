<!--
  Evidence for Rectification Tracker §11 — R6-006 / LV-R6-006-01
-->
# Goal

**Ordinary procurement users** (not only Administrator / auditor-style roles) must see the **simple readiness story first** on Tender Management — **business-readable labels** and summary status — while **Bundle / DSM / DOM / DEM / DCM** remain in the **collapsed technical drawer** until explicitly opened (Cursor pack **§12.6** acceptance: *“Tender user sees a simple readiness story first…”*).

# What was verified

| Layer | Check |
|-------|--------|
| **UI (Procurement Officer)** | **TM2 Tender** Desk form (`/app/tm2-tender/TND-MOH-2026-001`): **`tm2-tender-business-readiness-host`** mounts **`plc-business-readiness-summary`** with **Tender document readiness** + checklist (**Tender document package ready**); **`plc-br-technical-collapsed`** is closed; **`plc-br-business-checks`** precedes the technical `<details>` in DOM order. *(Management v2 workbench is often role-gated; the form uses the same readiness component as Overview — R6-002.)* |
| **API** | Session **`procurement.officer@moh.test`** receives **`can_view_technical_output_codes: true`**, **`summary_label`** matching business wording, and non-empty **`checks`** with **`business_label`**. |

# Evidence submitted (automated)

- Python: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.procurement_lifecycle.tests.test_r6_006_ordinary_user_readiness_business_labels`
- Playwright (from `apps/kentender_v1`): `npx playwright test tests/ui/smoke/procurement/ordinary_user_business_first_r6_006.spec.ts --workers=1` — **PLC-R6-006-01**

# Related references

- Pack **§12.6 Tender Management UI Patch** — default Overview business-readable readiness; technical evidence expandable.
- **R6-001** — `plc-business-readiness-summary` component; **R6-003** — collapsed technical drawer.
