# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The platform support issue (EVL-CHG-001 v0.4 §6, §5.1, §7.3 last row; plan
D12; owner decision OD-B; tracker EVL4-306). One issue per failed operation
identity, reused by every retry; assigned to the technical holders with a
work item; resolved only when the owner reports success; reopened (same
issue) if the operation fails again; never carrying business content."""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services import support_issues

NS = "SI_TEST"
HOLDER = "sit.holder@example.test"
OTHER = "sit.other@example.test"


class TestSupportIssues(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.addClassCleanup(cls._remove)
		from kentender_core.services import responsibility_administration as administration

		for email in (HOLDER, OTHER):
			if not frappe.db.exists("User", email):
				frappe.get_doc({"doctype": "User", "email": email, "first_name": "Support Test", "send_welcome_email": 0, "enabled": 1, "user_type": "System User"}).insert(
					ignore_permissions=True)
			frappe.get_doc("User", email).add_roles("Desk User")
		if not frappe.db.exists("User Responsibility Assignment", {"user": HOLDER, "business_role": "Technical Operator", "status": "Enabled"}):
			administration.grant(user=HOLDER, business_role="Technical Operator", organisation_unit="", fixture_namespace=NS, actor="Administrator")
		frappe.db.commit()

	@classmethod
	def _remove(cls):
		frappe.db.delete("Support Issue", {"fixture_namespace": NS})
		frappe.db.delete("Notification Log", {"for_user": ("in", (HOLDER, OTHER))})
		for email in (HOLDER, OTHER):
			frappe.db.delete("User Responsibility Assignment", {"user": email})
			if frappe.db.exists("User", email):
				frappe.delete_doc("User", email, force=True, ignore_permissions=True)
		frappe.db.commit()

	def setUp(self):
		self.addCleanup(lambda: frappe.db.delete("Support Issue", {"fixture_namespace": NS}))

	def open(self, correlation="EVL-INTAKE-TEST-1"):
		return support_issues.open_issue(module="Bid Evaluation", operation="ReceiveOpeningPackage", operation_correlation=correlation,
			subject="Resolve evaluation issue for TND-TEST-001", reference_doctype="Evaluation Case", reference_name="EVL-TEST-001",
			safe_detail="The completed opening package could not be loaded.", fixture_namespace=NS)

	def test_one_issue_per_operation_identity_assigned_to_the_holders(self):
		first = self.open()
		again = self.open()
		self.assertTrue(first["created"])
		self.assertFalse(again["created"])
		self.assertEqual(first["issue_id"], again["issue_id"])
		self.assertEqual(frappe.db.count("Support Issue", {"issue_key": "Bid Evaluation:EVL-INTAKE-TEST-1"}), 1)
		self.assertIn(HOLDER, first["holder_users"])
		self.assertNotIn(OTHER, first["holder_users"])
		self.assertEqual(first["notification_state"], "Delivered")
		rows = support_issues.my_work_rows(HOLDER)["assigned"]
		self.assertEqual([r["title"] for r in rows if r["reference"] == first["issue_id"]], ["Resolve evaluation issue for TND-TEST-001"])
		self.assertFalse([r for r in support_issues.my_work_rows(OTHER)["assigned"] if r["reference"] == first["issue_id"]])

	def test_only_success_resolves_and_a_new_failure_reopens_the_same_issue(self):
		issue = self.open()
		self.assertEqual(support_issues.get(issue["issue_id"])["status"], "Open")
		support_issues.resolve_on_success(module="Bid Evaluation", operation_correlation="EVL-INTAKE-TEST-1")
		self.assertEqual(support_issues.get(issue["issue_id"])["status"], "Resolved")
		self.assertFalse([r for r in support_issues.my_work_rows(HOLDER)["assigned"] if r["reference"] == issue["issue_id"]])
		reopened = self.open()
		self.assertEqual((reopened["issue_id"], reopened["status"]), (issue["issue_id"], "Open"))

	def test_no_business_content_fields(self):
		fields = {f.fieldname for f in frappe.get_meta("Support Issue").fields}
		self.assertFalse(fields & {"bid", "finding", "tenderer", "price", "submitted_total", "result"})
		with self.assertRaises(ValueError):
			support_issues.open_issue(module="Bid Evaluation", operation="x", operation_correlation="", subject="x", fixture_namespace=NS)
