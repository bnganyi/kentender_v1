# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-002 — Released list shows tender-created status labels."""

from __future__ import annotations

from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.released_to_tender import (
	get_pp_released_to_tender,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKG_TITLE,
	TENDER_CODE,
)


class TestPP3ReleasedListP7002(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
			self._skip = True
			return
		self._skip = False
		seed = seed_procurement_planning_works_master(checkpoint="CONSUMED_BY_TENDER", force_reset=True)
		if not seed.get("ok"):
			self.skipTest(f"WORKS master seed unavailable: {seed}")

	def test_pp7_002_list_includes_released_package_with_tender_created(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		out = get_pp_released_to_tender()
		self.assertTrue(out.get("ok"), msg=out)
		rows = out.get("rows") or []
		match = next(
			(r for r in rows if (r.get("package") or {}).get("code") == PKG_CODE),
			None,
		)
		self.assertIsNotNone(match, msg=f"Expected {PKG_CODE} in released list: {rows}")
		pkg = match.get("package") or {}
		self.assertEqual(pkg.get("name"), PKG_TITLE)
		tender = match.get("tender") or {}
		self.assertEqual(tender.get("code"), TENDER_CODE)
		consumption = match.get("consumption") or {}
		self.assertIn(consumption.get("status"), ("Consumed", "Not Consumed"))

	def test_pp7_002_list_row_status_label_contract(self) -> None:
		path = Path(frappe.get_app_path("kentender_procurement")) / "public" / "js" / "pp3_planning_released_list.js"
		with path.open(encoding="utf-8") as fh:
			source = fh.read()
		self.assertIn('data-testid="pp3-released-row-status"', source)
		self.assertIn("Released · Tender created", source)
