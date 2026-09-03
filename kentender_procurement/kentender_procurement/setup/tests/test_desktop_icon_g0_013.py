# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""G0-013 — Strategy / Budget Desktop Icons are role-gated (not globally hidden)."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase


class TestDesktopIconG013RoleGate(IntegrationTestCase):
	def test_strategy_desktop_icon_visible_only_to_matrix_roles(self):
		if not frappe.db.exists("Desktop Icon", "Strategy"):
			self.skipTest("Strategy Desktop Icon not on site")
		doc = frappe.get_doc("Desktop Icon", "Strategy")
		self.assertEqual(int(doc.hidden or 0), 0)
		roles = {r.role for r in (doc.roles or [])}
		self.assertEqual(
			roles,
			# "Strategy Manager" removed with the Role itself (STR-CHG-001 v1.7):
			# it named Strategy authority it never carried after the rebuild.
			{"System Manager", "Administrator", "Strategy Author"},
			msg="G0-011: Planning Authority must not get Strategy home tile; specialists above only.",
		)

	def test_budget_desktop_icon_visible_only_to_matrix_roles(self):
		if not frappe.db.exists("Desktop Icon", "Budget"):
			self.skipTest("Budget Desktop Icon not on site")
		doc = frappe.get_doc("Desktop Icon", "Budget")
		self.assertEqual(int(doc.hidden or 0), 0)
		roles = {r.role for r in (doc.roles or [])}
		self.assertEqual(
			roles,
			{"System Manager", "Administrator", "Planning Authority", "Finance Reviewer"},
		)

	def test_procurement_desktop_icon_remains_unrestricted(self):
		if not frappe.db.exists("Desktop Icon", "Procurement"):
			self.skipTest("Procurement Desktop Icon not on site")
		doc = frappe.get_doc("Desktop Icon", "Procurement")
		self.assertEqual(int(doc.hidden or 0), 0)
		self.assertFalse(
			bool(doc.roles),
			msg="Procurement tile must stay the primary entry for general roles (empty roles = all users).",
		)
