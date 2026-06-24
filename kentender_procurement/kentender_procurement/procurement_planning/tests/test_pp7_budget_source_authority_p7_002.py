# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-002 / PP2-REG-002 — Planning does not mutate budget line authority."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	budget_authority_snapshot,
	require_active_template,
	run_planning_pipeline_through_release,
	seed_budget_line,
)


class TestPP7BudgetSourceAuthorityP7002(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Budget Line"):
			self._skip = True
			return
		self._skip = False
		self._cleanup: list[tuple[str, str]] = []

	def tearDown(self):
		if getattr(self, "_skip", True):
			return
		frappe.set_user("Administrator")
		for doctype, name in reversed(self._cleanup):
			if doctype == "Procurement Journey":
				frappe.db.sql("DELETE FROM `tabProcurement Journey` WHERE name=%s", name)
				continue
			if frappe.db.exists(doctype, name):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
		frappe.db.commit()

	def test_pp7_002_planning_pipeline_preserves_budget_authority(self) -> None:
		if self._skip:
			self.skipTest("Budget Line not installed")
		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		bl_name, _, _, _ = seed_budget_line()
		if not bl_name:
			self.skipTest("No active budget line available")

		before = budget_authority_snapshot(bl_name)
		out = run_planning_pipeline_through_release(self._cleanup, with_release=True)
		after = budget_authority_snapshot(out["budget_line_name"])
		self.assertEqual(before, after, msg="Planning pipeline must not mutate budget authority fields")
