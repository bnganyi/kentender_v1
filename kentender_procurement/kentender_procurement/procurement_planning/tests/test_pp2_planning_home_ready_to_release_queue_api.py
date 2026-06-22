# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-005 — Planning Home Ready to Release queue API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_home import (
	get_pp_planning_home_ready_to_release_queue,
)
from kentender_procurement.procurement_planning.pp2_constants import PKG_READY_FOR_RELEASE
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	PLANNING_HOME_QUEUE_LIMIT,
	format_ready_to_release_work_item,
	get_ready_to_release_home_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	_count_ready_to_release,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2PlanningHomeReadyToReleaseQueueAPI(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_home_ready_to_release_queue()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_queue_shape(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_planning_home_ready_to_release_queue()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		self.assertEqual(out.get("queue_key"), "ready_to_release")
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
			self.assertEqual(primary.get("label"), "Open")
			self.assertEqual(primary.get("action"), "open_package")
			self.assertTrue(primary.get("target"))

	def test_service_matches_whitelisted_api_and_summary_filter(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		service_out = get_ready_to_release_home_queue("Administrator")
		api_out = get_pp_planning_home_ready_to_release_queue()
		self.assertEqual(service_out.get("total"), api_out.get("total"))
		self.assertEqual(service_out.get("items"), api_out.get("items"))
		self.assertEqual(api_out.get("total"), _count_ready_to_release("Administrator"))

	def test_service_rows_use_ready_release_filter(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_ready_to_release_home_queue("Administrator")
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		for item in out.get("items") or []:
			self.assertTrue(item.get("id"))


class TestPP2PlanningHomeReadyToReleaseWorkItemMapper(IntegrationTestCase):
	def test_subtitle_includes_category_method_and_value(self) -> None:
		item = format_ready_to_release_work_item(
			{
				"package": {
					"id": "PKG-001",
					"code": "PKG-MOH-2026-001",
					"name": "District Hospital Renovation Works",
				},
				"status": PKG_READY_FOR_RELEASE,
				"category": "Works",
				"method": "Open Tender",
				"estimated_value": 98000000,
				"currency": "KES",
			}
		)
		self.assertEqual(item["title"], "District Hospital Renovation Works")
		self.assertNotIn("PKG-MOH-2026-001", item["title"])
		self.assertIn("Works", item["subtitle"])
		self.assertIn("Open Tender", item["subtitle"])
		self.assertIn("KES", item["subtitle"])
		self.assertEqual(item["next_action_label"], "Release package")
		self.assertEqual(item["primary_action"]["label"], "Open")
		self.assertEqual(item["primary_action"]["target"], "PKG-001")

	def test_subtitle_omits_empty_segments(self) -> None:
		item = format_ready_to_release_work_item(
			{
				"package": {"id": "PKG-002", "code": "PKG-002", "name": "Office Supplies Package"},
				"status": PKG_READY_FOR_RELEASE,
				"category": "Goods",
				"method": "",
				"estimated_value": 0,
				"currency": "KES",
			}
		)
		self.assertIn("Goods", item["subtitle"])
		self.assertNotIn("Open Tender", item["subtitle"])
