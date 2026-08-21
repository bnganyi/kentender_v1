from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	OU, PE, REQUESTER, REVIEWER, upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.lifecycle import create_need, review_need, submit_need


class TestDepartmentalNeedsNotifications(IntegrationTestCase):
	"""NDS-CHG-002 Phase 9 (NDS-FR-037): submit/return/accept/decline create
	durable in-app Notification Log events. This was previously unimplemented —
	no notification call existed anywhere in the module."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-NOTIFY-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _create_and_submit(self):
		fy = self._current_fy()
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Notification test need {uuid4().hex[:8]}",
			business_justification="Phase 9 notification regression coverage exercising the submit-review lifecycle.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Field kits", "indicative_quantity": 5, "unit_code": "Set"}],
			idempotency_key=self._key("CREATE"), user=REQUESTER,
		)
		submitted = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=self._key("SUBMIT"), user=REQUESTER)
		return created, submitted

	def test_submit_notifies_the_departmental_reviewer(self):
		created, submitted = self._create_and_submit()
		rows = frappe.get_all(
			"Notification Log", filters={"for_user": REVIEWER, "document_type": "Departmental Need", "document_name": created["need"]},
			fields=["subject", "link"],
		)
		self.assertEqual(len(rows), 1)
		self.assertIn(created["need_reference"], rows[0].subject)
		self.assertIn(f"need={created['need']}", rows[0].link)

	def test_return_notifies_the_requester_not_the_reviewer(self):
		created, submitted = self._create_and_submit()
		task = frappe.get_doc("Workflow Task", submitted["task"])
		review_need(
			need=created["need"], decision="return", task=task.name,
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("RETURN"), reason="Clarify the delivery timeline before this can proceed to review.",
			user=REVIEWER,
		)
		requester_rows = frappe.get_all(
			"Notification Log", filters={"for_user": REQUESTER, "document_type": "Departmental Need", "document_name": created["need"]},
		)
		self.assertEqual(len(requester_rows), 1)
		# The reviewer only ever gets the one Submit notification, not a second one for their own Return decision.
		reviewer_rows = frappe.get_all(
			"Notification Log", filters={"for_user": REVIEWER, "document_type": "Departmental Need", "document_name": created["need"]},
		)
		self.assertEqual(len(reviewer_rows), 1)

	def test_accept_notifies_the_requester_and_is_idempotent(self):
		created, submitted = self._create_and_submit()
		task = frappe.get_doc("Workflow Task", submitted["task"])
		review_need(
			need=created["need"], decision="accept", task=task.name,
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("ACCEPT"), user=REVIEWER,
		)
		from kentender_procurement.departmental_needs.services.notifications import notify_need_transition
		doc = frappe.get_doc("Departmental Need", created["need"])
		first = notify_need_transition(doc, action="Accept for planning")
		second = notify_need_transition(doc, action="Accept for planning")
		self.assertEqual(first, second)
		self.assertEqual(
			frappe.db.count("Notification Log", {"for_user": REQUESTER, "document_type": "Departmental Need", "document_name": created["need"]}), 1,
		)
