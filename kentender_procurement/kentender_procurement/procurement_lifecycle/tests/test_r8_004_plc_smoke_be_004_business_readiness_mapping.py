# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R8-004 / LV-R8-BE-04 — PLC-SMOKE-BE-004: business readiness maps technical outputs.

Pack §15.1 / tracker §13:

    TM2 Tender readiness summary displays five business labels and preserves
    Bundle/DSM/DOM/DEM/DCM technical refs.

Uses **R3-016** ``get_business_readiness_summary`` after the same PLC path as **R8-001**
(dependencies **LV-R3-016-01** / **R3-016**).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
      --module kentender_procurement.procurement_lifecycle.tests.test_r8_004_plc_smoke_be_004_business_readiness_mapping

Companion evidence:
docs/prompts/0. usability handoff/R8_004_plc_smoke_be_004_evidence.md
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.seeds._common import ensure_currency_kes, ensure_procuring_entity
from kentender_strategy.seeds.works_master_strategy_hierarchy import (
    upsert_works_master_strategy_hierarchy,
)
from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget
from kentender_procurement.procurement_lifecycle.legacy_demand_seed_shim import (
    upsert_works_master_demand,
)
from kentender_procurement.procurement_planning.seeds.works_master_planning_seed import (
    upsert_works_master_planning,
)
from kentender_procurement.tender_management.seeds.works_master_std_seed import (
    upsert_works_master_std,
)
from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
    upsert_works_master_tender,
)
from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
    load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
    get_business_readiness_summary,
)

_PE_CODE = "PE-MOH"
_PE_DISPLAY = "Ministry of Health"

_WORKS_TENDER_CODE = "TND-MOH-2026-001"

# Align with R3-016 BRS-003 / BRS-004 / BRS-005 / BRS-006 and pack §13.
_EXPECTED_BUSINESS_LABELS = [
    "Tender document package ready",
    "Supplier submission checklist ready",
    "Opening register rules ready",
    "Evaluation rules ready",
    "Contract carry-forward terms ready",
]
_EXPECTED_TECH_LABELS = ["Bundle", "DSM", "DOM", "DEM", "DCM"]
_EXPECTED_TECH_REFS = {
    "Bundle": "GB-TND-MOH-2026-001-V2",
    "DSM": "DSM-TND-MOH-2026-001-V2",
    "DOM": "DOM-TND-MOH-2026-001-V2",
    "DEM": "DEM-TND-MOH-2026-001-V2",
    "DCM": "DCM-TND-MOH-2026-001-V2",
}
_EXPECTED_SNAPSHOT_REF = "PUBSNAP-TND-MOH-2026-001-V2"


class TestR8004PlcSmokeBe004BusinessReadinessMapping(IntegrationTestCase):
    """PLC-SMOKE-BE-004 — WORKS load + TM2 readiness summary shape (business ↔ technical)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        ensure_currency_kes()
        cls.pe_name = ensure_procuring_entity(_PE_CODE, _PE_DISPLAY)

        for label, fn in (
            ("Strategy", upsert_works_master_strategy_hierarchy),
            ("Budget", upsert_works_master_budget),
            ("Demand", upsert_works_master_demand),
            ("Planning", upsert_works_master_planning),
            ("STD", upsert_works_master_std),
            ("Tender", upsert_works_master_tender),
        ):
            result = fn()
            assert result.get("ok"), f"{label} seed failed: {result}"

        frappe.db.commit()

    def test_plc_smoke_be_004_readiness_maps_five_technical_and_snapshot(self):
        """PLC-SMOKE-BE-004 — five business labels, five technical refs, snapshot line."""
        load_out = load_procurement_lifecycle_works_master(
            reset=True,
            checkpoint="TENDER_PUBLISHED",
        )
        self.assertTrue(load_out.get("ok"), msg=f"PLC load failed: {load_out}")
        frappe.db.commit()

        result = get_business_readiness_summary("TM2 Tender", _WORKS_TENDER_CODE)

        self.assertEqual(result.get("object_type"), "TM2 Tender", msg=result)
        self.assertEqual(result.get("object_code"), _WORKS_TENDER_CODE, msg=result)
        self.assertEqual(result.get("status"), "Ready", msg=result)
        self.assertEqual(result.get("summary_label"), "Tender document readiness", msg=result)

        checks = result.get("checks") or []
        self.assertEqual(len(checks), 5, msg=result)
        for check in checks:
            self.assertEqual(check.get("result"), "PASS", msg=check)

        self.assertEqual(
            [c["business_label"] for c in checks],
            _EXPECTED_BUSINESS_LABELS,
            msg=result,
        )
        self.assertEqual(
            [c["technical_label"] for c in checks],
            _EXPECTED_TECH_LABELS,
            msg=result,
        )

        by_label = {c["technical_label"]: c for c in checks}
        for tech_label, expected_ref in _EXPECTED_TECH_REFS.items():
            row = by_label.get(tech_label)
            self.assertIsNotNone(row, msg=f"missing {tech_label} in {result!r}")
            self.assertEqual(row.get("technical_ref"), expected_ref, msg=row)

        self.assertEqual(
            result.get("snapshot_ref"),
            _EXPECTED_SNAPSHOT_REF,
            msg=result,
        )
        self.assertTrue(result.get("technical_details_available"), msg=result)
