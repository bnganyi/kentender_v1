# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P5C-002 — Planning Home summary counts API."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.api.planning_home import get_pp_planning_home_summary
from kentender_procurement.procurement_planning.services.planning_home_summary import (
	PLANNING_HOME_SUMMARY_KEYS,
	get_planning_home_summary,
)


def _pp_ok() -> bool:
	return bool(frappe.db.exists("DocType", "Procurement Plan"))


class TestPP2PlanningHomeSummaryAPI(IntegrationTestCase):
	def test_summary_keys_contract(self) -> None:
		self.assertEqual(
			PLANNING_HOME_SUMMARY_KEYS,
			(
				"needs_planning",
				"needs_review",
				"ready_to_release",
				"released_recently",
				"blocked",
			),
		)

	def test_guest_denied(self) -> None:
		frappe.set_user("Guest")
		out = get_pp_planning_home_summary()
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error_code"), "PP_ACCESS_DENIED")

	def test_administrator_summary_shape(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		out = get_pp_planning_home_summary()
		self.assertTrue(out.get("ok"), msg=out.get("message"))
		summary = out.get("summary") or {}
		for key in PLANNING_HOME_SUMMARY_KEYS:
			self.assertIn(key, summary)
			self.assertIsInstance(summary[key], int)
			self.assertGreaterEqual(summary[key], 0)

	def test_service_matches_whitelisted_api(self) -> None:
		if not _pp_ok():
			self.skipTest("Procurement Planning not installed")
		frappe.set_user("Administrator")
		service_out = get_planning_home_summary("Administrator")
		api_out = get_pp_planning_home_summary()
		self.assertEqual(service_out.get("summary"), api_out.get("summary"))
