# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""UI-00 dashboard API — dual arrays, summary, tab/filter behaviour."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_configurations import get_tender_configurations_dashboard
from kentender_procurement.tender_configurations.constants import (
	TAB_IN_PROGRESS,
	TAB_NEEDS_ATTENTION,
	TAB_READY_TO_CONFIGURE,
)
from kentender_procurement.tender_configurations.seed.ui00_seed import (
	clear_ui00_seed,
	seed_ui00_dashboard,
)


class TestTenderConfigurationDashboardApi(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		seed_ui00_dashboard(clear=True)

	@classmethod
	def tearDownClass(cls) -> None:
		clear_ui00_seed()
		super().tearDownClass()

	def setUp(self) -> None:
		frappe.set_user("Administrator")

	def test_ready_tab_returns_package_rows_only(self) -> None:
		out = get_tender_configurations_dashboard(tab=TAB_READY_TO_CONFIGURE)
		self.assertGreaterEqual(out["summary"]["ready_to_configure_count"], 2)
		self.assertTrue(out["ready_to_configure_packages"])
		self.assertEqual(out["configurations"], [])
		row = out["ready_to_configure_packages"][0]
		self.assertEqual(row["row_type"], "approved_procurement_package")
		self.assertIn("procurement_package_ref", row)
		self.assertNotIn("configuration_ref", row)
		self.assertEqual(row["action_label"], "Create Configuration")

	def test_in_progress_tab_returns_configuration_rows(self) -> None:
		out = get_tender_configurations_dashboard(tab=TAB_IN_PROGRESS)
		self.assertEqual(out["ready_to_configure_packages"], [])
		self.assertTrue(out["configurations"])
		row = out["configurations"][0]
		self.assertEqual(row["row_type"], "tender_configuration")
		self.assertIn("configuration_ref", row)
		self.assertIn("status_label", row)
		self.assertIn("issues_label", row)
		self.assertEqual(row["next_action_label"], "Continue Configuration")

	def test_summary_counts(self) -> None:
		out = get_tender_configurations_dashboard(tab=TAB_READY_TO_CONFIGURE)
		s = out["summary"]
		self.assertGreaterEqual(s["in_progress_count"], 1)
		self.assertGreaterEqual(s["needs_attention_count"], 1)
		self.assertGreaterEqual(s["ready_for_review_count"], 1)
		self.assertGreaterEqual(s["ready_for_publication_count"], 1)
		self.assertGreaterEqual(s["completed_count"], 1)

	def test_issue_filter_on_needs_attention(self) -> None:
		all_rows = get_tender_configurations_dashboard(tab=TAB_NEEDS_ATTENTION)
		blocked = get_tender_configurations_dashboard(
			tab=TAB_NEEDS_ATTENTION,
			issue_status="Has Blockers",
		)
		self.assertTrue(all_rows["configurations"])
		for row in blocked["configurations"]:
			self.assertGreater(row["blocker_count"], 0)

	def test_search_filters_packages(self) -> None:
		out = get_tender_configurations_dashboard(
			tab=TAB_READY_TO_CONFIGURE,
			search="Data Center",
		)
		refs = [r["procurement_package_ref"] for r in out["ready_to_configure_packages"]]
		self.assertTrue(any("READY-001" in r for r in refs))

	def test_filter_options_include_std_families(self) -> None:
		out = get_tender_configurations_dashboard()
		self.assertIn("Information Technology", out["filters"]["std_families"])
		self.assertIn("Works", out["filters"]["std_families"])
