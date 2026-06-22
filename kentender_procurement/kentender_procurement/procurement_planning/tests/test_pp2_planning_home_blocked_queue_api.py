# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-007 — Planning Home Blocked queue API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_home import (
	get_pp_planning_home_blocked_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	PLANNING_HOME_QUEUE_LIMIT,
	format_blocked_work_item,
	get_blocked_home_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	_count_blocked,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2PlanningHomeBlockedQueueAPI(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_home_blocked_queue()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_queue_shape(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_planning_home_blocked_queue()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		self.assertEqual(out.get("queue_key"), "blocked")
		self.assertIn("total", out)
		self.assertIn("limit", out)
		self.assertIn("items", out)
		self.assertIn("view_all_href", out)
		self.assertIsInstance(out.get("total"), int)
		self.assertEqual(out.get("limit"), PLANNING_HOME_QUEUE_LIMIT)
		items = out.get("items") or []
		self.assertIsInstance(items, list)
		self.assertLessEqual(len(items), PLANNING_HOME_QUEUE_LIMIT)
		total = int(out.get("total") or 0)
		self.assertGreaterEqual(total, len(items))
		for item in items:
			self.assertIn("title", item)
			self.assertIn("subtitle", item)
			self.assertIn("next_action_label", item)
			primary = item.get("primary_action") or {}
			self.assertEqual(primary.get("label"), "Resolve blocker")
			self.assertIn(primary.get("action"), ("open_demand", "open_package"))
			self.assertTrue(primary.get("target"))

	def test_service_matches_whitelisted_api_and_summary_filter(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		service_out = get_blocked_home_queue("Administrator")
		api_out = get_pp_planning_home_blocked_queue()
		self.assertEqual(service_out.get("total"), api_out.get("total"))
		self.assertEqual(service_out.get("items"), api_out.get("items"))
		self.assertEqual(api_out.get("total"), _count_blocked("Administrator"))


class TestPP2PlanningHomeBlockedWorkItemMapper(IntegrationTestCase):
	def test_mapper_for_blocked_demand(self) -> None:
		item = format_blocked_work_item(
			{
				"blocked_type": "demand",
				"demand": {
					"id": "DEM-001",
					"code": "DEM-MOH-2026-001",
					"name": "District Hospital Renovation Works Demand",
				},
				"category": "Works",
				"estimated_value": 98000000,
				"currency": "KES",
				"blocker_message": "Missing approved budget link",
			}
		)
		self.assertEqual(item["title"], "District Hospital Renovation Works Demand")
		self.assertEqual(item["next_action_label"], "Resolve blocker")
		self.assertIn("Missing approved budget link", item["subtitle"])
		self.assertEqual(item["primary_action"]["label"], "Resolve blocker")
		self.assertEqual(item["primary_action"]["action"], "open_demand")
		self.assertEqual(item["primary_action"]["target"], "DEM-001")

	def test_mapper_for_blocked_package(self) -> None:
		item = format_blocked_work_item(
			{
				"blocked_type": "package",
				"package": {
					"id": "PKG-001",
					"code": "PKG-MOH-2026-001",
					"name": "Regional Clinic Equipment Package",
				},
				"category": "Goods",
				"method": "Open Tender",
				"estimated_value": 12500000,
				"currency": "KES",
				"blocker_message": "Readiness checks failed",
			}
		)
		self.assertEqual(item["title"], "Regional Clinic Equipment Package")
		self.assertEqual(item["next_action_label"], "Resolve blocker")
		self.assertIn("Readiness checks failed", item["subtitle"])
		self.assertEqual(item["primary_action"]["label"], "Resolve blocker")
		self.assertEqual(item["primary_action"]["action"], "open_package")
		self.assertEqual(item["primary_action"]["target"], "PKG-001")
