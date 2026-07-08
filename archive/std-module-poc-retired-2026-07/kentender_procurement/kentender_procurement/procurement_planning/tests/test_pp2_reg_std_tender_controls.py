# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PP2-REG-4 / PP2-REG-004 — Planning release does not bypass STD/TM publication controls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.services.package_release_service import (
	release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.tests.pp2_reg_regression_helpers import (
	require_active_template,
	run_planning_pipeline_through_release,
)


class TestPP7StdTenderControlsP2Reg4(IntegrationTestCase):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Procurement Package"):
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

	def test_pp2_reg_004_release_does_not_publish_tender_or_complete_std_readiness(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		out = run_planning_pipeline_through_release(self._cleanup, with_release=False)
		package_code = out["package_code"]
		pub_before = frappe.db.count("TM2 Publication Record")
		std_ready_before = frappe.db.count("TM2 Publication Readiness", {"readiness_status": "Ready"})

		deliver = MagicMock()
		xmv = MagicMock()
		xmv.has_critical.return_value = False
		with patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=deliver,
			package_has_release_tender=MagicMock(return_value=True),
			validate_package_for_release_xmv=MagicMock(return_value=xmv),
		):
			rel = release_package_to_tender_management(package_code, "Administrator")

		self.assertTrue(rel.get("ok"), rel)
		release_code = rel.get("release_code") or ""
		if release_code:
			self._cleanup.append(("Procurement Handoff Card", release_code))

		pub_after = frappe.db.count("TM2 Publication Record")
		std_ready_after = frappe.db.count("TM2 Publication Readiness", {"readiness_status": "Ready"})
		self.assertEqual(pub_before, pub_after)
		self.assertEqual(std_ready_before, std_ready_after)
		deliver.assert_called_once()
