# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-INT-005 — PP2 demand navigation uses current Demands Desk routes."""

from pathlib import Path

from frappe.tests import UnitTestCase


def _router_source() -> str:
	path = Path(__file__).resolve().parents[2] / "public" / "js" / "pp2_planning_router.js"
	return path.read_text(encoding="utf-8", errors="replace")


class TestDemInt005PP2DemandRoutes(UnitTestCase):
	def setUp(self) -> None:
		super().setUp()
		self.source = _router_source()

	def test_removed_demand_routes_are_absent(self) -> None:
		for retired_route in ("demand-workbench", "demand-hub", "create-demand"):
			self.assertNotIn(retired_route, self.source)

	def test_approved_demand_rows_open_demand_detail(self) -> None:
		self.assertEqual(self.source.count('frappe.set_route("demand-detail"'), 2)
		self.assertEqual(self.source.count('"/desk/demand-detail/" + encodeURIComponent('), 2)

	def test_pp2_does_not_fall_back_to_raw_demand_doctype(self) -> None:
		self.assertNotIn('"/app/demand/"', self.source)
