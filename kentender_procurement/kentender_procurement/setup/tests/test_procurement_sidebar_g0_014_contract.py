# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-014 — Configuration specialist links (Strategy / Budget full workspaces) in repo export."""

from __future__ import annotations

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

_STRATEGY_FULL = "Strategy Alignment (full)"
_BUDGET_FULL = "Budget & Funding (full)"
_STRATEGY_DEPS = "frappe.user.has_role(['System Manager', 'Administrator', 'Strategy Manager'])"
_BUDGET_DEPS = "frappe.user.has_role(['System Manager', 'Administrator', 'Planning Authority', 'Finance Reviewer'])"


class TestProcurementSidebarG014SpecialistLinks(IntegrationTestCase):
	def test_procurement_sidebar_has_gated_specialist_workspace_links(self):
		path = os.path.join(
			frappe.get_app_path("kentender_procurement"),
			"workspace_sidebar",
			"procurement.json",
		)
		self.assertTrue(os.path.isfile(path), msg=f"Missing sidebar export: {path}")
		with open(path, encoding="utf-8") as f:
			data = json.load(f)
		items = data.get("items") or []
		by_label = {row.get("label"): row for row in items}
		self.assertIn(_STRATEGY_FULL, by_label, msg="Missing G0-014 Strategy specialist link under Configuration")
		self.assertIn(_BUDGET_FULL, by_label, msg="Missing G0-014 Budget specialist link under Configuration")
		s_row = by_label[_STRATEGY_FULL]
		b_row = by_label[_BUDGET_FULL]
		self.assertEqual((s_row.get("link_type"), s_row.get("link_to")), ("Workspace", "Strategy Management"))
		self.assertEqual((b_row.get("link_type"), b_row.get("link_to")), ("Workspace", "Budget Management"))
		self.assertEqual(s_row.get("display_depends_on"), _STRATEGY_DEPS)
		self.assertEqual(b_row.get("display_depends_on"), _BUDGET_DEPS)
