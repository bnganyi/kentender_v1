# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-003 — Planning Home Needs Planning queue API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_home import (
	get_pp_planning_home_needs_planning_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	NEEDS_PLANNING_HOME_LIMIT,
	format_needs_planning_work_item,
	get_needs_planning_home_queue,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2PlanningHomeNeedsPlanningQueueAPI(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_home_needs_planning_queue()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_queue_shape(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_planning_home_needs_planning_queue()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		self.assertEqual(out.get("queue_key"), "needs_planning")
		self.assertIn("total", out)
		self.assertIn("limit", out)
		self.assertIn("items", out)
		self.assertIn("view_all_href", out)
		self.assertIsInstance(out.get("total"), int)
		self.assertEqual(out.get("limit"), NEEDS_PLANNING_HOME_LIMIT)
		items = out.get("items") or []
		self.assertIsInstance(items, list)
		self.assertLessEqual(len(items), NEEDS_PLANNING_HOME_LIMIT)
		total = int(out.get("total") or 0)
		self.assertGreaterEqual(total, len(items))
		for item in items:
			self.assertIn("title", item)
			self.assertIn("subtitle", item)
			self.assertIn("next_action_label", item)
			primary = item.get("primary_action") or {}
			self.assertEqual(primary.get("label"), "Open")
			self.assertEqual(primary.get("action"), "open_demand")
			self.assertTrue(primary.get("target"))

	def test_service_matches_whitelisted_api(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		service_out = get_needs_planning_home_queue("Administrator")
		api_out = get_pp_planning_home_needs_planning_queue()
		self.assertEqual(service_out.get("total"), api_out.get("total"))
		self.assertEqual(service_out.get("items"), api_out.get("items"))


class TestPP2PlanningHomeNeedsPlanningWorkItemMapper(IntegrationTestCase):
	def test_subtitle_includes_category_value_and_funding(self) -> None:
		item = format_needs_planning_work_item(
			{
				"demand": {"id": "DEM-001", "code": "DEM-MOH-2026-001", "name": "District Hospital Renovation Works"},
				"category": "Works",
				"estimated_value": 98000000,
				"currency": "KES",
				"budget_line": {"id": "BL-1", "code": "BL-MOH-001", "name": "Capital Works"},
			}
		)
		self.assertEqual(item["title"], "District Hospital Renovation Works")
		self.assertIn("Works", item["subtitle"])
		self.assertIn("KES", item["subtitle"])
		self.assertIn("Budget linked", item["subtitle"])
		self.assertEqual(item["next_action_label"], "Include in procurement plan")
		self.assertEqual(item["primary_action"]["label"], "Open")
		self.assertEqual(item["primary_action"]["target"], "DEM-001")

	def test_subtitle_omits_funding_when_no_budget_line(self) -> None:
		item = format_needs_planning_work_item(
			{
				"demand": {"id": "DEM-002", "code": "DEM-MOH-2026-002", "name": "Office Supplies"},
				"category": "Goods",
				"estimated_value": 50000,
				"currency": "KES",
				"budget_line": {},
			}
		)
		self.assertNotIn("Budget linked", item["subtitle"])
		self.assertIn("Goods", item["subtitle"])
