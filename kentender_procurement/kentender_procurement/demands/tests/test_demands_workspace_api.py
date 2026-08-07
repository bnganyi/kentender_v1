# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DEM-UI-01 workspace API contract."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.demands.api import list_demands_workspace


class TestDemandsWorkspaceApi(FrappeTestCase):
	def test_list_demands_workspace_shape(self):
		frappe.set_user("Administrator")
		payload = list_demands_workspace(page=1, page_size=20)
		self.assertTrue(payload.get("ok"))
		self.assertIn("summary", payload)
		self.assertIn("rows", payload)
		summary = payload["summary"]
		for key in ("my_drafts", "returned_to_me", "my_approvals", "budget_confirmations"):
			self.assertIn(key, summary)
			self.assertIsInstance(summary[key], int)
		self.assertIsInstance(payload["rows"], list)
		self.assertEqual(payload["page"], 1)
		self.assertLessEqual(len(payload["rows"]), 20)
