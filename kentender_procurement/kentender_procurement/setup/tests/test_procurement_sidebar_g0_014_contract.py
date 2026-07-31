# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-014 — Configuration specialist links are Disabled for deployment (hidden).

Availability state *disabled_for_deployment* removes Configuration and its
children from the Procurement rail. Specialist workspace links are not shown
in the menu; authorization remains a separate concern.
"""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_STRATEGY_FULL = "Strategy Alignment (full)"
_BUDGET_FULL = "Budget & Funding (full)"


class TestProcurementSidebarG014SpecialistLinks(IntegrationTestCase):
	def test_configuration_specialist_links_hidden_for_deployment(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing sidebar export: {path}")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		labels = {row.get("label") for row in data.get("items") or []}
		self.assertNotIn("Configuration", labels)
		self.assertNotIn(_STRATEGY_FULL, labels)
		self.assertNotIn(_BUDGET_FULL, labels)
		self.assertNotIn("Procurement Templates", labels)
