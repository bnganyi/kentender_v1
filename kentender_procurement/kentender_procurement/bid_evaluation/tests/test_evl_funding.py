# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Funding beside the comparison (EVL-CHG-001 v0.5 §4.4; AUD-EVL-014).

Budget is read through its published funding read, never as the session user,
and a read that cannot be completed is a typed Unavailable fact that qualifies
the report, never a silent absence."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from kentender_procurement.bid_evaluation.services import funding

SEAM = "kentender_procurement.tenders.services.evaluation_seam.funding_reservations"
READ = "kentender_budget.services.budget_funding_read.read_reservation_funding"
ONE = {"reservation_ids": ["RSV-1"], "authorised_value": None}


def known(*remaining):
	return {"known": True, "missing": [], "rows": [{"id": f"RSV-{n}", "code": f"RSV-{n}", "status": "Active", "original_amount": r, "remaining_amount": r}
		for n, r in enumerate(remaining, 1)]}


class TestFundingRead(IntegrationTestCase):
	def test_a_shortfall_is_reported_beside_the_recommendation(self):
		with patch(SEAM, return_value=ONE), patch(READ, return_value=known("40.00", "10.00")):
			out = funding.compare("T", Decimal("100"))
		self.assertEqual((out["available"], out["shortfall"], out["qualification"]), (Decimal("50.00"), Decimal("50.00"), "Funding needs resolution before award."))
		with patch(SEAM, return_value=ONE), patch(READ, return_value=known("150.00")):
			self.assertEqual(funding.compare("T", Decimal("100"))["qualification"], "")

	def test_a_failed_read_is_a_typed_unavailable_fact_not_an_absence(self):
		with patch(SEAM, return_value=ONE), patch(READ, side_effect=frappe_permission_error()):
			out = funding.compare("T", Decimal("100"))
		self.assertEqual((out["status"], out["available"], out["shortfall"]), ("Unavailable", None, None))
		self.assertEqual(out["qualification"], funding.UNAVAILABLE_QUALIFICATION)

	def test_a_reservation_budget_cannot_find_is_unavailable_too(self):
		unknown = {"known": False, "rows": [], "missing": ["RSV-1"]}
		with patch(SEAM, return_value=ONE), patch(READ, return_value=unknown):
			out = funding.compare("T", Decimal("100"))
		self.assertEqual((out["status"], out["qualification"]), ("Unavailable", funding.UNAVAILABLE_QUALIFICATION))

	def test_a_tender_with_no_recorded_reservation_has_no_funding_fact(self):
		with patch(SEAM, return_value={"reservation_ids": [], "authorised_value": None}):
			self.assertIsNone(funding.compare("T", Decimal("100")))


def frappe_permission_error():
	import frappe

	return frappe.PermissionError("No read access to Procurement Budget Version")
