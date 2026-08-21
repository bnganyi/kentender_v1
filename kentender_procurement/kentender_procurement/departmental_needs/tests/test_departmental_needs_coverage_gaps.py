from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, now_datetime

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	OU, PE, REQUESTER, REVIEWER, upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.context import resolve_creation_context
from kentender_procurement.departmental_needs.services.lifecycle import create_need, review_need, submit_need, update_need
from kentender_procurement.departmental_needs.services.workspace import get_support_need, get_workspace


class TestDepartmentalNeedsCoverageGaps(IntegrationTestCase):
	"""NDS-CHG-002 Phase 9 (NDC-901): closes coverage-map gaps found while
	building the full FR/AC coverage map — NDS-FR-021's "one effective
	assignment is fixed automatically; multiple assignments require explicit
	selection" had zero prior test coverage for either branch on the
	multiple-assignments side."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _second_requester_assignment(self) -> str:
		"""A second Organisation Unit under the same Procuring Entity, with the
		Requester profile also assigned to Grace there — so Grace genuinely has
		2 active create-eligible contexts, not 1."""
		code = f"NDS-COV-{uuid4().hex[:6]}".upper()
		if not frappe.db.exists("Organisation Unit", code):
			frappe.get_doc({
				"doctype": "Organisation Unit", "unit_code": code, "unit_name": "Second directorate for NDS-FR-021 coverage",
				"unit_type": "OUT-DIRECTORATE", "procuring_entity": PE, "status": "Active",
			}).insert(ignore_permissions=True)
		profile = frappe.db.get_value("Operational Scope Assignment", "OSA-NDS-GRACE-MOH-DHP", "capability_profile_id")
		assignment_id = "OSA-NDS-COV-GRACE-SECOND-OU"
		if not frappe.db.exists("Operational Scope Assignment", assignment_id):
			frappe.get_doc({
				"doctype": "Operational Scope Assignment", "assignment_id": assignment_id, "user_id": REQUESTER,
				"capability_profile_id": profile, "procuring_entity_id": PE, "organisation_unit_id": code,
				"effective_from": add_days(now_datetime(), -1), "status": "Active",
				"assigned_by": "Administrator", "assigned_at": now_datetime(), "concurrency_token": uuid4().hex,
			}).insert(ignore_permissions=True)
		return code

	def test_multiple_assignments_require_explicit_selection_on_create_context(self):
		second_ou = self._second_requester_assignment()
		ctx = resolve_creation_context(user=REQUESTER)
		self.assertTrue(ctx["ok"])
		self.assertTrue(ctx["requires_selection"])
		self.assertEqual(
			sorted(row["organisation_unit"] for row in ctx["contexts"]), sorted([OU, second_ou]),
		)

	def test_multiple_assignments_require_explicit_selection_on_workspace(self):
		self._second_requester_assignment()
		result = get_workspace(user=REQUESTER)
		self.assertFalse(result["ok"])
		self.assertEqual(result["outcome"], "CONTEXT_SELECTION_REQUIRED")
		self.assertGreaterEqual(len(result["contexts"]), 2)

	# NDS-FR-041/AC-035 — a stale record_version fails without overwriting
	# current data. Also previously untested for any command.
	def test_stale_concurrency_token_is_rejected_without_overwriting_data(self):
		fy = next(row for row in enabled_fiscal_years() if row["is_current"])
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title="Original title", idempotency_key=f"TEST-NDS-COV-STALE-{uuid4().hex}", user=REQUESTER,
		)
		stale_token = created["concurrency_token"]
		# A second, real edit advances the token past what the caller still holds.
		update_need(
			need=created["need"], title="Updated by a second editor", expected_token=stale_token,
			idempotency_key=f"TEST-NDS-COV-STALE-2-{uuid4().hex}", user=REQUESTER,
		)
		with self.assertRaises(DepartmentalNeedError) as ctx:
			update_need(
				need=created["need"], title="Stale overwrite attempt", expected_token=stale_token,
				idempotency_key=f"TEST-NDS-COV-STALE-3-{uuid4().hex}", user=REQUESTER,
			)
		self.assertEqual(ctx.exception.code, "NDS_CONCURRENCY_CONFLICT")
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "title"), "Updated by a second editor")

	# §12 "Client repeats the same submit request" — only create_need's
	# idempotency was directly tested; submit_need has its own extra
	# complexity (execute_routed_transition's own idempotency check,
	# separate from _existing()) that was never itself exercised twice.
	def test_repeated_submit_request_returns_the_original_result_without_duplicate_effect(self):
		fy = next(row for row in enabled_fiscal_years() if row["is_current"])
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"], title="Repeat-submit coverage need",
			business_justification="Exercises submit_need's own idempotency path independently of create_need's.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Field kits", "indicative_quantity": 5, "unit_code": "Set"}],
			idempotency_key=f"TEST-NDS-COV-REPEAT-CREATE-{uuid4().hex}", user=REQUESTER,
		)
		key = f"TEST-NDS-COV-REPEAT-SUBMIT-{uuid4().hex}"
		first = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=key, user=REQUESTER)
		second = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=key, user=REQUESTER)
		self.assertFalse(first["idempotent"])
		self.assertTrue(second["idempotent"])
		self.assertEqual(first["task"], second["task"])
		self.assertEqual(frappe.db.count("Departmental Need Review", {"departmental_need": created["need"], "action": "Submit"}), 1)
		self.assertEqual(frappe.db.count("Workflow Task", {"subject_type": "Departmental Need", "subject_id": created["need"]}), 1)

	# §12 "System Administrator opens a Need with support reason" — audited
	# read-only view, no operational action. get_support_need()'s own wiring
	# to the shared support-read gate was never directly exercised by this
	# module's own test suite.
	def test_support_reason_grants_audited_read_only_administrator_access(self):
		before = frappe.db.count("Audit Event", {"event_type": "authorization.support_record_view"})
		result = get_support_need(need="NDS-MOH-2027-002", purpose="Investigating a reported access issue.", user="Administrator")
		self.assertTrue(result["ok"])
		self.assertEqual(result["access_label"], "Support read-only")
		self.assertEqual(result["actions"], [])
		self.assertEqual(frappe.db.count("Audit Event", {"event_type": "authorization.support_record_view"}), before + 1)

	# NDS-FR-032/AC-029 and NDS-FR-035/AC-032 — a mandatory 20-1,000 character
	# reason for Return/Decline. Only enforced client-side (the reason
	# dialog's minlength/maxlength) before this fix; a direct API call with a
	# 1-character reason was previously accepted.
	def test_review_decision_rejects_a_reason_shorter_than_twenty_characters(self):
		fy = next(row for row in enabled_fiscal_years() if row["is_current"])
		created = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"], title="Short-reason coverage need",
			business_justification="Exercises the server-side 20-1,000 character reason floor for Return/Decline decisions.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Field kits", "indicative_quantity": 5, "unit_code": "Set"}],
			idempotency_key=f"TEST-NDS-COV-SHORTREASON-CREATE-{uuid4().hex}", user=REQUESTER,
		)
		submitted = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=f"TEST-NDS-COV-SHORTREASON-SUBMIT-{uuid4().hex}", user=REQUESTER)
		task = frappe.get_doc("Workflow Task", submitted["task"])
		with self.assertRaises(DepartmentalNeedError) as ctx:
			review_need(
				need=created["need"], decision="return", task=task.name,
				expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
				idempotency_key=f"TEST-NDS-COV-SHORTREASON-{uuid4().hex}", reason="too short", user=REVIEWER,
			)
		self.assertEqual(ctx.exception.code, "NDS_REASON_INVALID")
		self.assertEqual(frappe.db.get_value("Departmental Need", created["need"], "status"), "Submitted")
