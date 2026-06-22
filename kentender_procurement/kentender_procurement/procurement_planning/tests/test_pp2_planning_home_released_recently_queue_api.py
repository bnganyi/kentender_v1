# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-006 — Planning Home Released Recently queue API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_home import (
	get_pp_planning_home_released_recently_queue,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.services.planning_home_queues import (
	PLANNING_HOME_QUEUE_LIMIT,
	format_released_recently_work_item,
	get_released_recently_home_queue,
)
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	_count_released_recently,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2PlanningHomeReleasedRecentlyQueueAPI(IntegrationTestCase):
	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_home_released_recently_queue()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_queue_shape(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_planning_home_released_recently_queue()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		self.assertEqual(out.get("queue_key"), "released_recently")
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
			self.assertEqual(primary.get("label"), "Open Tender")
			self.assertEqual(primary.get("action"), "open_tender")
			self.assertTrue(primary.get("target"))
			secondary = item.get("secondary_actions") or []
			self.assertIsInstance(secondary, list)
			self.assertGreaterEqual(len(secondary), 1)
			self.assertEqual(secondary[0].get("label"), "View Package")
			self.assertEqual(secondary[0].get("action"), "open_package")

	def test_service_matches_whitelisted_api_and_summary_filter(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		service_out = get_released_recently_home_queue("Administrator")
		api_out = get_pp_planning_home_released_recently_queue()
		self.assertEqual(service_out.get("total"), api_out.get("total"))
		self.assertEqual(service_out.get("items"), api_out.get("items"))
		self.assertEqual(api_out.get("total"), _count_released_recently("Administrator"))


class TestPP2PlanningHomeReleasedRecentlyWorkItemMapper(IntegrationTestCase):
	def test_mapper_for_consumed_package(self) -> None:
		item = format_released_recently_work_item(
			{
				"package": {
					"id": "PKG-001",
					"code": "PKG-MOH-2026-001",
					"name": "District Hospital Renovation Works",
				},
				"status": PKG_CONSUMED,
				"tender": {
					"id": "TND-MOH-2026-001",
					"code": "TND-MOH-2026-001",
					"name": "District Hospital Renovation Works Tender",
				},
			}
		)
		self.assertEqual(item["title"], "District Hospital Renovation Works")
		self.assertEqual(item["subtitle"], "Released to Tender Management · Tender created")
		self.assertEqual(item["next_action_label"], "Continue in Tender Management")
		self.assertEqual(item["primary_action"]["label"], "Open Tender")
		self.assertEqual(item["primary_action"]["action"], "open_tender")
		self.assertEqual(item["primary_action"]["target"], "TND-MOH-2026-001")
		self.assertEqual(item["secondary_actions"][0]["label"], "View Package")
		self.assertEqual(item["secondary_actions"][0]["action"], "open_package")
		self.assertEqual(item["secondary_actions"][0]["target"], "PKG-001")

	def test_mapper_for_released_package_without_tender(self) -> None:
		item = format_released_recently_work_item(
			{
				"package": {"id": "PKG-002", "code": "PKG-002", "name": "Regional Clinic Equipment"},
				"status": PKG_RELEASED,
				"tender": {},
			}
		)
		self.assertEqual(item["title"], "Regional Clinic Equipment")
		self.assertEqual(item["subtitle"], "Released to Tender Management")
		self.assertEqual(item["primary_action"]["label"], "Open Tender")
		self.assertEqual(item["primary_action"]["action"], "open_tender")
		self.assertEqual(item["primary_action"]["target"], "PKG-002")
