# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""ensure_budget_workspace() — canonical Budget Management Workspace identity."""

from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_budget.services.budget_workspace import (
	CANONICAL_NAME,
	LEGACY_NAME,
	ensure_budget_workspace,
)


class TestBudgetWorkspaceIdentity(FrappeTestCase):
	def tearDown(self):
		"""Leave the shared canonical Workspace in place, correctly named — other
		suites and the live site depend on Budget Management resolving; never delete it."""
		if frappe.db.exists("Workspace", LEGACY_NAME):
			frappe.delete_doc("Workspace", LEGACY_NAME, force=1, ignore_permissions=True)
		ensure_budget_workspace()
		frappe.db.commit()

	def _assert_canonical(self):
		self.assertTrue(frappe.db.exists("Workspace", CANONICAL_NAME))
		self.assertFalse(frappe.db.exists("Workspace", LEGACY_NAME))
		row = frappe.db.get_value(
			"Workspace",
			CANONICAL_NAME,
			["name", "label", "public", "is_hidden"],
			as_dict=True,
		)
		self.assertEqual(row.name, CANONICAL_NAME)
		self.assertEqual(row.label, LEGACY_NAME)
		self.assertEqual(int(row.public or 0), 1)
		self.assertEqual(int(row.is_hidden or 0), 0)

	def test_creates_canonical_when_neither_exists(self):
		for name in (CANONICAL_NAME, LEGACY_NAME):
			if frappe.db.exists("Workspace", name):
				frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)

		ensure_budget_workspace()

		self._assert_canonical()

	def test_renames_legacy_named_workspace(self):
		if frappe.db.exists("Workspace", CANONICAL_NAME):
			frappe.delete_doc("Workspace", CANONICAL_NAME, force=1, ignore_permissions=True)
		if not frappe.db.exists("Workspace", LEGACY_NAME):
			frappe.get_doc(
				{
					"doctype": "Workspace",
					"label": LEGACY_NAME,
					"title": LEGACY_NAME,
					"module": "Kentender Budget",
					"app": "kentender_budget",
					"type": "Workspace",
					"content": "[]",
					"public": 0,
					"is_hidden": 0,
				}
			).insert(ignore_permissions=True)

		ensure_budget_workspace()

		self._assert_canonical()

	def test_repeated_calls_do_not_duplicate(self):
		ensure_budget_workspace()
		ensure_budget_workspace()

		self._assert_canonical()
		self.assertEqual(
			frappe.db.count("Workspace", {"name": ["in", [CANONICAL_NAME, LEGACY_NAME]]}), 1
		)

	def test_normalizes_mismatched_label_on_existing_canonical(self):
		"""Simulates a cross-app fixture creating the row with the wrong label/module."""
		if frappe.db.exists("Workspace", CANONICAL_NAME):
			frappe.delete_doc("Workspace", CANONICAL_NAME, force=1, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Workspace",
				"label": CANONICAL_NAME,
				"title": CANONICAL_NAME,
				"module": "Kentender Procurement",
				"app": "kentender_procurement",
				"type": "Workspace",
				"content": "[]",
				"public": 0,
				"is_hidden": 0,
			}
		).insert(ignore_permissions=True, set_name=CANONICAL_NAME)

		ensure_budget_workspace()

		self._assert_canonical()
		self.assertEqual(
			frappe.db.get_value("Workspace", CANONICAL_NAME, "module"), "Kentender Budget"
		)

	def test_procurement_sidebar_link_resolves_after_helper_runs(self):
		if frappe.db.exists("Workspace", CANONICAL_NAME):
			frappe.delete_doc("Workspace", CANONICAL_NAME, force=1, ignore_permissions=True)

		ensure_budget_workspace()

		self.assertTrue(frappe.db.exists("Workspace", CANONICAL_NAME))
