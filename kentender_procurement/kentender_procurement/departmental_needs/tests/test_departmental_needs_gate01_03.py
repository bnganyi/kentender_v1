from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import (
	OU, PE, PLANNER, REQUESTER, REVIEWER, upsert_departmental_needs,
)
from kentender_procurement.departmental_needs.services.lifecycle import (
	approve_withdrawal, create_need, request_withdrawal, review_need, submit_need,
)
from kentender_procurement.departmental_needs.services.usage import planning_usage
from kentender_procurement.departmental_needs.services.workspace import get_workspace


class TestDepartmentalNeedsGate0103(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _create(self):
		fy = self._current_fy()
		return create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Lifecycle need {uuid4().hex[:8]}", business_justification="A governed lifecycle test requirement.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Training cohort", "indicative_quantity": 10, "unit": "staff"}],
			idempotency_key=self._key("CREATE"), user=REQUESTER,
		)

	def test_schema_is_greenfield_and_excludes_procurement_controls(self):
		for doctype in ("Departmental Need", "Departmental Need Item", "Departmental Need Review", "Plan Need Allocation"):
			self.assertTrue(frappe.db.exists("DocType", doctype))
			self.assertEqual(frappe.get_meta(doctype).permissions, [])
		meta = frappe.get_meta("Departmental Need")
		for forbidden in ("procurement_method", "procurement_category", "funding_reservation", "requisition"):
			self.assertIsNone(meta.get_field(forbidden))

	def test_exact_workspace_fixture_and_separate_usage(self):
		result = get_workspace(procuring_entity=PE, organisation_unit=OU, financial_year="2027/28", user=REVIEWER)
		self.assertTrue(result["ok"])
		self.assertEqual(result["summary"], {"total_needs": 3, "awaiting_departmental_review": 1, "accepted_for_planning": 1, "included_in_approved_plan": 1})
		self.assertEqual([row["reference"] for row in result["work_requiring_action"]], ["NDS-MOH-2027-002"])
		self.assertEqual(planning_usage("NDS-MOH-2027-001"), "Fully included")
		self.assertEqual(frappe.db.get_value("Departmental Need", "NDS-MOH-2027-001", "status"), "Accepted for planning")

	def test_submit_review_and_accepted_withdrawal_are_task_gated(self):
		created = self._create()
		submitted = submit_need(need=created["need"], expected_token=created["concurrency_token"], idempotency_key=self._key("SUBMIT"), user=REQUESTER)
		task = frappe.get_doc("Workflow Task", submitted["task"])
		accepted = review_need(need=created["need"], decision="accept", task=task.name,
			expected_token=submitted["concurrency_token"], task_token=task.concurrency_token,
			idempotency_key=self._key("ACCEPT"), user=REVIEWER)
		request = request_withdrawal(need=created["need"], expected_token=accepted["concurrency_token"], reason="Requirement is no longer needed.",
			idempotency_key=self._key("WITHDRAW-REQUEST"), user=REQUESTER)
		self.assertEqual(request["status"], "Accepted for planning")
		withdrawal_task = frappe.get_doc("Workflow Task", request["task"])
		withdrawn = approve_withdrawal(need=created["need"], task=withdrawal_task.name,
			expected_token=request["concurrency_token"], task_token=withdrawal_task.concurrency_token,
			idempotency_key=self._key("WITHDRAW-APPROVE"), user=REVIEWER)
		self.assertEqual(withdrawn["status"], "Withdrawn")
		self.assertEqual(frappe.db.count("Departmental Need Review", {"departmental_need": created["need"]}), 5)

	def test_idempotent_create_and_future_year_fail_closed(self):
		fy = self._current_fy()
		key = self._key("IDEMPOTENT")
		kwargs = dict(procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"], title="Idempotent Need",
			business_justification="Test", required_by_date=fy["end_date"], delivery_or_use_location="MOH",
			items=[{"description": "One unit", "indicative_quantity": 1, "unit": "sets"}], idempotency_key=key, user=REQUESTER)
		first, second = create_need(**kwargs), create_need(**kwargs)
		self.assertEqual(first["need"], second["need"])
		self.assertTrue(second["idempotent"])
		future = next((row for row in enabled_fiscal_years() if row["is_future"]), None)
		if future:
			with self.assertRaises(DepartmentalNeedError) as caught:
				create_need(**{**kwargs, "target_financial_year": future["id"], "idempotency_key": self._key("FUTURE")})
			self.assertEqual(caught.exception.code, "NDS_INTAKE_WINDOW_NOT_CONFIGURED")

	def test_planner_sees_only_accepted_sources_and_cannot_edit(self):
		result = get_workspace(procuring_entity=PE, organisation_unit=OU, financial_year="2027/28", user=PLANNER)
		self.assertEqual([row["reference"] for row in result["needs"]], ["NDS-MOH-2027-001"])
		self.assertTrue(all(row["actions"] == [{"code": "view", "label": "View"}] for row in result["needs"]))
