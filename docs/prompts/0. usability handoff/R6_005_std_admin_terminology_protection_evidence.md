<!--
  Evidence for Rectification Tracker §11 — R6-005 / LV-R6-005-01
-->
# Goal

R6 business-readiness labelling on Tender Management must **not** replace **Official STD Library** governance terminology on **`std-engine`**. Administrators must still see the **official library** framing, primary import actions, queue labels (**Active STDs**, **Package Imports**, etc.), and guidance that references **structured packages**, **evidence**, and **immutability** (Cursor pack **§12.5**).

# Scope reviewed

| Concern | Protection |
|--------|------------|
| Primary STD Admin concept | **Official STD Library** headline + governance guidance strip (mirrors R5-008 separation). |
| TM2 / R6 bleed | No **`plc-business-readiness-summary`** and no “Tender document readiness” copy inside **`data-testid="std-library-page"`** — automated in Playwright. |
| Source contract | **`std_library_shell.js`** retains translated governance strings; Python test fails if copy is removed or business-readiness markers are inlined. |

# Evidence submitted (automated)

- Python: `bench --site kentender.midas.com run-tests --app kentender_procurement --module kentender_procurement.setup.tests.test_r6_005_std_admin_terminology_protection`
- Playwright (from `apps/kentender_v1`): `npx playwright test tests/ui/smoke/procurement/std_admin_terminology_r6_005.spec.ts --workers=1` — **PLC-R6-005-01**

# Related references

- Pack **§12.5 STD Admin UI Patch** — Official STD Library primary; usage panel; no tender-runtime-as-default.  
- R5-008 baseline: [`R5_008_official_STD_library_separation_evidence.md`](./R5_008_official_STD_library_separation_evidence.md)
