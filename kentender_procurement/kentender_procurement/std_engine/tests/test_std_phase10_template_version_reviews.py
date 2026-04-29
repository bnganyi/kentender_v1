from __future__ import annotations

import frappe

from kentender_procurement.std_engine.api.template_version_workbench import (
	get_std_template_version_reviews_approval,
)
from kentender_procurement.std_engine.services.template_version_reviews_service import (
	build_std_template_version_reviews_approval,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR1013TemplateVersionReviewsApproval(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		super().tearDown()

	def test_not_found(self):
		out = build_std_template_version_reviews_approval("NO-SUCH-VERSION-999")
		self.assertFalse(out.get("ok"))
		self.assertEqual(out.get("error"), "not_found")

	def test_whitelist_rejects_guest(self):
		try:
			frappe.set_user("Guest")
			self.assertRaises(frappe.PermissionError, get_std_template_version_reviews_approval, self.version_code)
		finally:
			frappe.set_user("Administrator")

	def test_whitelist_returns_for_admin(self):
		out = get_std_template_version_reviews_approval(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertIn("activation_checklist", out)
		self.assertEqual(len(out.get("activation_checklist") or []), 15)
		self.assertIn("activation_legal_immutability_text", out)
		self.assertIn("activation_gates", out)

	def test_active_version_read_only_and_ui_block_reason(self):
		out = build_std_template_version_reviews_approval(self.version_code)
		self.assertTrue(out.get("ok"))
		self.assertTrue(out.get("read_only"))
		self.assertIn("immutable", (out.get("activation_ui_block_reason") or "").lower())

	def test_returned_corrections_when_legal_returned(self):
		name = frappe.db.get_value("STD Template Version", {"version_code": self.version_code}, "name")
		frappe.db.set_value("STD Template Version", name, "legal_review_status", "Returned")
		try:
			out = build_std_template_version_reviews_approval(self.version_code)
			self.assertTrue(out.get("ok"))
			ret = out.get("returned_corrections") or []
			self.assertTrue(any(r.get("source") == "legal" for r in ret))
		finally:
			frappe.db.set_value("STD Template Version", name, "legal_review_status", "Approved")
