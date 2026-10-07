# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""RG-31 — a Plan Item Correction Request is read inside the scope of the plan
item it concerns. A Head of User Department could read every request over REST
because the doctype had no scope hook; now a Head reads the requests over items
their own department contributes to, and the Site-wide Planning readers (Planner,
Head of Procurement Function, Auditor) and technical readers keep reading all."""

from __future__ import annotations

import frappe

from kentender_core.services.responsibility_administration import grant, revoke
from kentender_procurement.procurement_planning.services import plan_requisition
from kentender_procurement.procurement_planning.tests import fixtures as fx
from kentender_procurement.procurement_planning.tests.test_plan_requisition import RequisitionCase, key

DOCTYPE = "Plan Item Correction Request"


class TestCorrectionRequestReadScope(RequisitionCase):
	def setUp(self):
		super().setUp()
		_accepted, item_id = self.active_item()
		frappe.set_user(fx.HOD)  # Head of User Department of OU_ALPHA, the item's contributing unit
		self.request = plan_requisition.receive_plan_item_correction_request(
			plan_item_id=item_id, requisition_reference="REQ-TEST-SCOPE-1", requisition_version="RQV-TEST-SCOPE-1",
			reason="The authorised warranty period does not match the department's actual need.",
			idempotency_key=key(),
		)["correction_request"]
		frappe.set_user("Administrator")
		# a Head of User Department of the OTHER unit
		granted = grant(
			user=fx.OUTSIDER, business_role="Head of User Department", organisation_unit=fx.OU_BETA,
			fixture_namespace=fx.NS, actor="Administrator",
		)
		if granted.get("created"):
			self.addCleanup(revoke, granted["assignment"], reason="Test-only revocation of a disposable head.", actor="Administrator")

	def listed(self, user: str) -> set[str]:
		return {row.name for row in frappe.get_list(DOCTYPE, user=user, limit_page_length=0)}

	def readable(self, user: str) -> bool:
		frappe.set_user(user)
		try:
			return bool(frappe.has_permission(DOCTYPE, "read", doc=self.request))
		finally:
			frappe.set_user("Administrator")

	def test_the_head_of_a_contributing_department_reads_it(self):
		self.assertIn(self.request, self.listed(fx.HOD))
		self.assertTrue(self.readable(fx.HOD))

	def test_the_head_of_another_department_does_not(self):
		self.assertNotIn(self.request, self.listed(fx.OUTSIDER))
		self.assertFalse(self.readable(fx.OUTSIDER))
		frappe.set_user(fx.OUTSIDER)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(DOCTYPE, self.request).check_permission("read")

	def test_the_site_wide_planning_readers_and_technical_readers_read_it(self):
		for user in (fx.PLANNER, fx.HOPF, fx.AUDITOR, "Administrator"):
			with self.subTest(user=user):
				self.assertIn(self.request, self.listed(user))
				self.assertTrue(self.readable(user))
