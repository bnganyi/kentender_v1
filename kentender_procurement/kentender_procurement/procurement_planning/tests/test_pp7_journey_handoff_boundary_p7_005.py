# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-005 / PP2-REG-005 — Journey/Handoff layer cannot override Planning package state."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.pp2_constants import PKG_APPROVED
from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	require_active_template,
	run_planning_pipeline_through_release,
)


class TestPP7JourneyHandoffBoundaryP7005(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Journey"):
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

	def test_pp7_005_handoff_and_journey_mutations_do_not_change_package_status(self) -> None:
		if self._skip:
			self.skipTest("Procurement Journey not installed")
		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		out = run_planning_pipeline_through_release(
			self._cleanup, with_release=False, through="approved"
		)
		package_code = out["package_code"]
		journey_code = out["journey_code"]
		inclusion_code = out["inclusion_code"]
		before_status = frappe.db.get_value("Procurement Package", package_code, "status")
		self.assertEqual(before_status, PKG_APPROVED)

		if inclusion_code and frappe.db.exists("Procurement Handoff Card", inclusion_code):
			frappe.db.set_value(
				"Procurement Handoff Card",
				inclusion_code,
				{"status": "Consumed", "next_action": "Simulated handoff override"},
				update_modified=True,
			)

		if journey_code and frappe.db.exists("Procurement Journey", journey_code):
			frappe.db.set_value(
				"Procurement Journey",
				journey_code,
				{
					"current_stage_key": "tender_published",
					"current_stage_label": "Tender Published",
					"current_status_category": "Completed",
				},
				update_modified=True,
			)

		after_status = frappe.db.get_value("Procurement Package", package_code, "status")
		self.assertEqual(after_status, before_status)
