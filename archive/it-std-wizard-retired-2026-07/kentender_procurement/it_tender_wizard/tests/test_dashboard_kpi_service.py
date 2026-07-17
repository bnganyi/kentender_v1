# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ITW-BE-DASH-003 — Dashboard KPI service (Screen 01 v2 four-card contract)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.it_tender_wizard.api.instance_api import get_dashboard_summary
from kentender_procurement.it_tender_wizard.services.dashboard_kpi_service import (
	DASHBOARD_STATUS_FILTERS,
	build_dashboard_filter_options,
	build_dashboard_summary,
)
from kentender_procurement.patches.it_wizard_dashboard_seed import seed_dashboard_sample_instances
from kentender_procurement.std_engine.constants import CANONICAL_PACKAGE_ID


class TestDashboardKpiService(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		if not frappe.db.exists("STD Version", CANONICAL_PACKAGE_ID):
			cls.skipTest("STD Version not on site")
		seed_dashboard_sample_instances()
		frappe.set_user("Administrator")

	def test_kpi_counts_match_seeded_states_four_card_contract(self) -> None:
		summary = build_dashboard_summary()
		kpis = summary["kpis"]
		self.assertEqual(
			set(kpis.keys()),
			{"in_configuration", "needs_action", "ready_for_review", "publication_ready"},
		)
		self.assertGreaterEqual(kpis["in_configuration"], 1)
		# VALIDATION_FAILED + RETURNED_FOR_CORRECTION seeds
		self.assertGreaterEqual(kpis["needs_action"], 2)
		self.assertGreaterEqual(kpis["ready_for_review"], 1)

	def test_today_deltas_never_exceed_kpi_totals(self) -> None:
		summary = build_dashboard_summary()
		for key, total in summary["kpis"].items():
			self.assertLessEqual(summary["today_deltas"][key], total)

	def test_filter_options_include_all_dashboard_statuses(self) -> None:
		options = build_dashboard_filter_options()
		status_values = {row["value"] for row in options["statuses"]}
		self.assertEqual(status_values, {code for code, _ in DASHBOARD_STATUS_FILTERS})
		self.assertTrue(any(row["name"] == "Ministry of ICT" for row in options["entities"]))
		self.assertTrue(any(row["name"] == "Open Tender" for row in options["methods"]))

	def test_dashboard_summary_api_returns_filter_options(self) -> None:
		payload = get_dashboard_summary()
		self.assertTrue(payload["success"])
		data = payload["data"]
		self.assertIn("filter_options", data)
		self.assertIn("today_deltas", data)
		self.assertEqual(len(data["filter_options"]["statuses"]), 4)
		self.assertEqual(
			set(data["kpis"].keys()),
			{"in_configuration", "needs_action", "ready_for_review", "publication_ready"},
		)
