# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""STD UI alignment — role-scoped workbench chrome (landing payload)."""

from __future__ import annotations

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.std_engine.api.landing import get_std_workbench_kpi_strip, search_std_workbench_objects


class TestSTDWorkbenchChromeVisibility(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def test_administrator_gets_full_governance_policy(self):
		payload = get_std_workbench_kpi_strip()
		self.assertTrue(payload.get("ok"))
		self.assertEqual("full_governance", payload.get("visibility_policy"))
		self.assertEqual(7, len(payload.get("scope_tabs") or []))
		self.assertEqual(8, len(payload.get("kpis") or []))

	def test_procurement_officer_only_gets_instance_operational_surface(self):
		# Patch role resolution only — do not patch frappe.get_roles globally or DB counts run with wrong identity.
		with patch(
			"kentender_procurement.std_engine.api.landing._stdlib_role_names",
			return_value={"Procurement Officer"},
		):
			payload = get_std_workbench_kpi_strip()
		self.assertTrue(payload.get("ok"))
		self.assertEqual("instance_operational", payload.get("visibility_policy"))
		tabs = payload.get("scope_tabs") or []
		self.assertEqual(
			{"mywork", "instances", "generation_jobs", "addendum_impacts", "audit_view"},
			{x.get("id") for x in tabs},
		)
		self.assertNotIn("templates", {x.get("id") for x in tabs})
		self.assertLessEqual(len(payload.get("kpis") or []), 8)
		self.assertGreaterEqual(len(payload.get("kpis") or []), 1)

	def test_instance_operator_cannot_search_governance_only_scope(self):
		with patch(
			"kentender_procurement.std_engine.api.landing._stdlib_role_names",
			return_value={"Procurement Officer"},
		):
			with self.assertRaises(frappe.PermissionError):
				search_std_workbench_objects(scope_tab_id="templates", queue_id="draft_versions")
