# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P7-003 / PP2-REG-003 — Tender creation requires valid Planning Release Package."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.procurement_planning.package_planning_release_display import (
	pkgrel_handoff_code_from_journey_code,
)
from kentender_procurement.procurement_planning.services.package_release_service import (
	release_package_to_tender_management,
)
from kentender_procurement.procurement_planning.tests.pp7_regression_helpers import (
	require_active_template,
	run_planning_pipeline_through_release,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.create_tender_from_package import (
	create_tender_from_package,
)


class TestPP7TenderCreationBoundaryP7003(IntegrationTestCase):
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

	def test_pp7_003_unreleased_package_cannot_create_tender(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		out = run_planning_pipeline_through_release(
			self._cleanup, with_release=False, through="package"
		)
		package_code = out["package_code"]
		status = frappe.db.get_value("Procurement Package", package_code, "status")
		self.assertEqual(status, "Draft")

		spec = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec)
		assert spec is not None
		deny = create_tender_from_package(
			"Administrator",
			package_code,
			context={"granted_permissions": [spec.required_permission]},
		)
		self.assertFalse(deny.get("ok"))
		self.assertEqual(deny.get("denial_code"), DenialCode.PACKAGE_NOT_AUTHORIZED.value)

	def test_pp7_003_release_creates_pkgrel_handoff(self) -> None:
		if self._skip:
			self.skipTest("Procurement Package not installed")
		if not require_active_template():
			self.skipTest("No active Procurement Template with profiles available")

		out = run_planning_pipeline_through_release(
			self._cleanup, with_release=False, through="ready"
		)
		package_code = out["package_code"]
		journey_code = out["journey_code"]
		expected_release = pkgrel_handoff_code_from_journey_code(journey_code)

		xmv = MagicMock()
		xmv.has_critical.return_value = False
		with patch.multiple(
			"kentender_procurement.procurement_planning.services.package_release_service",
			deliver_procurement_package_release=MagicMock(),
			package_has_release_tender=MagicMock(return_value=True),
			validate_package_for_release_xmv=MagicMock(return_value=xmv),
		):
			rel = release_package_to_tender_management(package_code, "Administrator")

		self.assertTrue(rel.get("ok"), rel)
		self.assertEqual(rel.get("release_code"), expected_release)
		self.assertTrue(frappe.db.exists("Procurement Handoff Card", expected_release))
		self._cleanup.append(("Procurement Handoff Card", expected_release))
