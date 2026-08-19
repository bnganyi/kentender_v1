from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.seeds._common import ensure_procuring_entity
from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	BUDGET_VIEWER, OU, PE, REQUESTER, REVIEWER, upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.lifecycle import create_need, review_need, submit_need
from kentender_procurement.departmental_needs.services.permissions import require_create
from kentender_procurement.departmental_needs.services.workspace import get_workspace

MODULE_SOURCE_DIR = Path(__file__).resolve().parent.parent


class TestDepartmentalNeedsCompletenessGaps(IntegrationTestCase):
	"""Closes NDS-AC gaps flagged by the 19 Aug 2026 audit: AC-005, AC-007, AC-008, AC-015, AC-002/AC-019."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-GAP-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _create_and_submit(self, *, user=REQUESTER):
		fy = self._current_fy()
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Gap-closure need {uuid4().hex[:8]}", business_justification="Completeness-gap regression coverage.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Field kits", "indicative_quantity": 5, "unit": "sets"}],
			idempotency_key=self._key("CREATE"), user=user,
		)
		submitted = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=self._key("SUBMIT"), user=user)
		return created, submitted

	def _ensure_delegate(self) -> str:
		"""A Departmental Review Delegate acts via an Authorization Delegation FROM the
		Head of User Department, not an independent scope assignment — the review task
		is routed to a named assignee (the reviewer), and only an active delegation lets
		another user act on that reviewer's open tasks (see _task_allows / _active_delegations
		in kentender_core.services.authorization_policy)."""
		email = "nds.delegate@moh.example.test"
		if not frappe.db.exists("User", email):
			frappe.get_doc({
				"doctype": "User", "email": email, "first_name": "Delegate", "last_name": "Reviewer",
				"enabled": 1, "user_type": "System User", "send_welcome_email": 0,
			}).insert(ignore_permissions=True)
		frappe.get_doc("User", email).add_roles("Desk User", "Departmental Review Delegate")
		reviewer_profile = frappe.db.get_value("Operational Scope Assignment", "OSA-NDS-PETER-MOH-DHP", "capability_profile_id")
		delegation_id = "AUD-NDS-DELEGATE-TEST"
		if not frappe.db.exists("Authorization Delegation", delegation_id):
			frappe.get_doc({
				"doctype": "Authorization Delegation", "delegation_id": delegation_id,
				"delegator_user_id": REVIEWER, "delegate_user_id": email, "capability_profile_id": reviewer_profile,
				"procuring_entity_id": PE, "organisation_unit_id": OU,
				"effective_from": add_days(now_datetime(), -1), "effective_to": add_days(now_datetime(), 7),
				"reason": "Test coverage for NDS-AC-005 delegate-scoped review.", "status": "Active",
				"approved_by": "Administrator", "approved_at": now_datetime(), "concurrency_token": uuid4().hex,
			}).insert(ignore_permissions=True)
		return email

	def _foreign_ou(self, pe: str, label: str) -> str:
		code = f"NDS-GAP-{label}-{uuid4().hex[:6]}".upper()
		frappe.get_doc({
			"doctype": "Organisation Unit", "unit_code": code, "unit_name": f"Foreign {label} for NDS gap closure",
			"unit_type": "OUT-DIRECTORATE", "procuring_entity": pe, "status": "Active",
		}).insert(ignore_permissions=True)
		return code

	# RBD-404 — AC-005: an explicitly delegated Departmental Review Delegate can perform scoped review.
	def test_departmental_review_delegate_can_perform_scoped_review(self):
		delegate = self._ensure_delegate()
		created, submitted = self._create_and_submit()
		task = frappe.get_doc("Workflow Task", submitted["task"])
		accepted = review_need(
			need=created["need"], decision="accept", task=task.name,
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("DELEGATE-ACCEPT"), user=delegate,
		)
		self.assertEqual(accepted["status"], "Accepted for planning")
		actor = frappe.db.get_value(
			"Departmental Need Review",
			{"departmental_need": created["need"], "action": "Accept for planning"},
			"actor",
		)
		self.assertEqual(actor, delegate)

	# RBD-405 — AC-007: acceptance creates no funding/reservation/requisition side effects.
	def test_accept_creates_no_funding_reservation_or_requisition_side_effects(self):
		self.assertFalse(frappe.db.exists("DocType", "Procurement Requisition"))
		before = frappe.db.count("Funding Reservation") if frappe.db.exists("DocType", "Funding Reservation") else 0
		created, submitted = self._create_and_submit()
		task = frappe.get_doc("Workflow Task", submitted["task"])
		accepted = review_need(
			need=created["need"], decision="accept", task=task.name,
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("ACCEPT-NOEFFECT"), user=REVIEWER,
		)
		self.assertEqual(accepted["status"], "Accepted for planning")
		after = frappe.db.count("Funding Reservation") if frappe.db.exists("DocType", "Funding Reservation") else 0
		self.assertEqual(before, after)

	# RBD-406 — AC-008: Budget Officers have no command action in Departmental Needs.
	def test_budget_officer_cannot_review_a_need(self):
		created, submitted = self._create_and_submit()
		task = frappe.get_doc("Workflow Task", submitted["task"])
		with self.assertRaises(frappe.PermissionError):
			review_need(
				need=created["need"], decision="accept", task=task.name,
				expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
				idempotency_key=self._key("BUDGET-DENY"), user=BUDGET_VIEWER,
			)
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "status"), "Submitted")

	# RBD-407 — AC-015: no Departmental Needs source file references Requisition or Tender doctypes.
	def test_no_source_file_references_requisition_or_tender_doctypes(self):
		forbidden = ("Procurement Requisition", '"Tender"', "'Tender'")
		hits: list[tuple[str, str]] = []
		for path in MODULE_SOURCE_DIR.rglob("*.py"):
			if "tests" in path.relative_to(MODULE_SOURCE_DIR).parts or path.name.startswith("test_"):
				continue
			text = path.read_text()
			hits.extend((str(path), token) for token in forbidden if token in text)
		self.assertEqual(hits, [])

	# RBD-408 — AC-002/AC-019: cross-PE and cross-department access fail closed.
	def test_cross_pe_and_cross_department_access_fail_closed(self):
		fy = self._current_fy()
		foreign_pe = ensure_procuring_entity("PE-NDS-GAP-TEST", "Foreign Test Entity for NDS gap closure")
		foreign_pe_ou = self._foreign_ou(foreign_pe, "PE")
		with self.assertRaises(frappe.PermissionError):
			require_create(REQUESTER, foreign_pe, foreign_pe_ou, fy["id"])

		foreign_ou_under_moh = self._foreign_ou(PE, "OU")
		with self.assertRaises(frappe.PermissionError):
			require_create(REQUESTER, PE, foreign_ou_under_moh, fy["id"])

		with self.assertRaises(DepartmentalNeedError) as caught:
			get_workspace(procuring_entity=PE, organisation_unit=foreign_ou_under_moh, financial_year=fy["id"], user=REQUESTER)
		self.assertEqual(caught.exception.code, "NDS_CONTEXT_OUTSIDE_ASSIGNMENT")
