from __future__ import annotations

from uuid import uuid4

import frappe
from frappe.tests import IntegrationTestCase

from kentender_core.services.financial_context import enabled_fiscal_years
from kentender_procurement.departmental_needs.constants import STATE_DRAFT
from kentender_procurement.departmental_needs.errors import DepartmentalNeedError
from kentender_procurement.departmental_needs.seeds.kentender_mvp_r1 import OU, PE, REQUESTER, upsert_departmental_needs
from kentender_procurement.departmental_needs.services.lifecycle import create_need, submit_need


class TestDepartmentalNeedsSubmissionValidation(IntegrationTestCase):
	"""NDS-CHG-002 §5 submission validation contract (Phase 3)."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		upsert_departmental_needs()

	def _key(self, label: str) -> str:
		return f"TEST-NDS-VAL-{label}-{uuid4().hex}"

	def _current_fy(self):
		return next(row for row in enabled_fiscal_years() if row["is_current"])

	def _complete_kwargs(self, fy, **overrides):
		kwargs = dict(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Validation need {uuid4().hex[:8]}",
			business_justification="A complete business justification long enough to satisfy the fifty character minimum.",
			required_by_date=fy["end_date"], delivery_or_use_location="Digital Health Directorate",
			items=[{"description": "Training cohort", "indicative_quantity": 10, "unit_code": "Staff"}],
			idempotency_key=self._key("CREATE"), user=REQUESTER,
		)
		kwargs.update(overrides)
		return kwargs

	def test_partial_draft_save_succeeds_with_only_context_and_title(self):
		"""NDS-FR-023 / NDS-AC-023 — a Draft may be saved with only context + title valid."""
		fy = self._current_fy()
		result = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Bare draft {uuid4().hex[:8]}", idempotency_key=self._key("PARTIAL"), user=REQUESTER,
		)
		self.assertTrue(result["ok"])
		self.assertEqual(result["status"], STATE_DRAFT)
		doc = frappe.get_doc("Departmental Need", result["need"])
		self.assertEqual(doc.business_justification, "")
		self.assertIsNone(doc.required_by_date)
		self.assertEqual(doc.delivery_or_use_location, "")
		self.assertEqual(frappe.db.count("Departmental Need Item", {"departmental_need": doc.name}), 0)

	def test_partial_draft_save_accepts_an_incomplete_item_row(self):
		"""An item row with only a description (no quantity/unit yet) is a valid Draft state."""
		fy = self._current_fy()
		result = create_need(
			procuring_entity=PE, organisation_unit=OU, target_financial_year=fy["id"],
			title=f"Incomplete item draft {uuid4().hex[:8]}",
			items=[{"description": "Still deciding quantity"}],
			idempotency_key=self._key("PARTIAL-ITEM"), user=REQUESTER,
		)
		self.assertTrue(result["ok"])
		row = frappe.db.get_value(
			"Departmental Need Item", {"departmental_need": result["need"]}, ["description", "indicative_quantity", "unit_code"], as_dict=True,
		)
		self.assertEqual(row.description, "Still deciding quantity")
		self.assertEqual(row.unit_code, "")

	def _assert_submit_fails_as_noop(self, need_result, **override_kwargs):
		before_status = frappe.db.get_value("Departmental Need", need_result["need"], "status")
		before_revision = frappe.db.get_value("Departmental Need", need_result["need"], "revision_no")
		before_reviews = frappe.db.count("Departmental Need Review", {"departmental_need": need_result["need"]})
		with self.assertRaises(DepartmentalNeedError):
			submit_need(
				need=need_result["need"], expected_token=need_result["concurrency_token"],
				idempotency_key=self._key("SUBMIT-FAIL"), user=REQUESTER,
			)
		self.assertEqual(frappe.db.get_value("Departmental Need", need_result["need"], "status"), before_status)
		self.assertEqual(frappe.db.get_value("Departmental Need", need_result["need"], "revision_no"), before_revision)
		self.assertEqual(frappe.db.count("Departmental Need Review", {"departmental_need": need_result["need"]}), before_reviews)

	def test_submit_rejects_short_justification(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, business_justification="Too short."))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_missing_required_by_date(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, required_by_date=None))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_required_by_date_outside_target_year(self):
		fy = self._current_fy()
		out_of_year = frappe.utils.add_days(fy["end_date"], 30)
		result = create_need(**self._complete_kwargs(fy, required_by_date=out_of_year))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_missing_location(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, delivery_or_use_location=""))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_zero_items(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, items=[]))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_an_incomplete_item_row(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, items=[{"description": "Missing quantity and unit"}]))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_non_two_decimal_indicative_cost(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, indicative_cost=1000.999))
		self._assert_submit_fails_as_noop(result)

	def test_submit_rejects_negative_indicative_cost(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, indicative_cost=-500))
		self._assert_submit_fails_as_noop(result)

	def test_submit_succeeds_with_a_fully_complete_need(self):
		fy = self._current_fy()
		result = create_need(**self._complete_kwargs(fy, indicative_cost=1000.50))
		submitted = submit_need(need=result["need"], expected_token=result["concurrency_token"], idempotency_key=self._key("SUBMIT-OK"), user=REQUESTER)
		self.assertTrue(submitted["ok"])
		self.assertEqual(submitted["revision_no"], 1)
