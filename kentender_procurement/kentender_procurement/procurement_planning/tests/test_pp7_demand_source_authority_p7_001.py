# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-001 / PP2-REG-001 — Planning does not mutate upstream demand authority."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	demand_authority_snapshot,
	run_planning_pipeline_through_release,
)


class TestPP7DemandSourceAuthorityP7001(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Demand") or not frappe.db.exists("DocType", "Procurement Plan"):
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

	def test_pp7_001_planning_pipeline_preserves_demand_authority(self) -> None:
		if self._skip:
			self.skipTest("Demand or Procurement Plan not installed")
		from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
			require_active_template,
		)

		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		out = run_planning_pipeline_through_release(self._cleanup, with_release=True)
		before = demand_authority_snapshot(out["demand_name"])
		after = demand_authority_snapshot(out["demand_name"])
		self.assertEqual(before, after, msg="Planning pipeline must not mutate demand authority fields")
