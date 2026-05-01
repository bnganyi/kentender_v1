# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Procurement Officer Tender Configuration POC — Officer step 6 BoQ readiness.

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_officer_poc_step6_boq_readiness
"""

from __future__ import annotations

import json
from pathlib import Path

from frappe.tests import UnitTestCase

from kentender_procurement.tender_management.services.officer_tender_config import (
	get_officer_boq_readiness_summary,
)


def _primary_configuration_and_boq() -> tuple[dict, list]:
	repo = Path(__file__).resolve().parents[4]
	path = (
		repo
		/ "kentender_procurement"
		/ "kentender_procurement"
		/ "tender_management"
		/ "std_templates"
		/ "ke_ppra_works_building_2022_04_poc"
		/ "sample_tender.json"
	)
	data = json.loads(path.read_text(encoding="utf-8"))
	return dict(data["configuration"]), list(data["boq"]["rows"])


class TestOfficerPocStep6BoqReadiness(UnitTestCase):
	def test_primary_sample_has_dayworks_and_provisional_when_required(self) -> None:
		cfg, rows = _primary_configuration_and_boq()
		out = get_officer_boq_readiness_summary(cfg, rows)
		self.assertEqual(out["missing_required_categories"], [])
		self.assertEqual(out["boq_row_count"], 9)
		self.assertIn("DAYWORKS", out["categories"])
		self.assertIn("PROVISIONAL_SUMS", out["categories"])

	def test_missing_dayworks_surfaces_warning(self) -> None:
		cfg, rows = _primary_configuration_and_boq()
		cfg["WORKS.DAYWORKS_INCLUDED"] = True
		filtered = [r for r in rows if r.get("item_category") != "DAYWORKS"]
		out = get_officer_boq_readiness_summary(cfg, filtered)
		self.assertIn("DAYWORKS", out["missing_required_categories"])
		self.assertTrue(any("DAYWORKS" in w for w in out["warnings"]))

	def test_invalid_lot_reference_detected(self) -> None:
		cfg, rows = _primary_configuration_and_boq()
		bad = list(rows)
		bad[0] = {**bad[0], "lot_code": "LOT-UNKNOWN"}
		out = get_officer_boq_readiness_summary(
			cfg, bad, existing_lot_codes=frozenset({"LOT-001", "LOT-002"})
		)
		self.assertTrue(out["invalid_lot_refs"])
