# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-27 — ``tender_management.immutability_guards`` (doc 9 §5.4).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_immutability_guards_p1_27
"""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.tender_management.immutability_guards import only_supersede_pointer_dicts
from kentender_procurement.tender_management.tests.test_release_procurement_package_to_tender_b3 import (
	_ReleaseProcurementPackageHandoffFixtures,
)
from kentender_procurement.tender_management.tests.test_tm2_bid_submission_p1_15 import (
	_TM2BidSubmissionP115FixtureMixin,
)


class TestImmutabilityGuardsDictP127(unittest.TestCase):
	def test_p127_only_supersede_pointer_dicts_positive(self) -> None:
		prev = {"a": 1, "ptr": ""}
		curr = {"a": 1, "ptr": "NEW-READINESS"}
		self.assertTrue(only_supersede_pointer_dicts(prev, curr, pointer="ptr"))

	def test_p127_only_supersede_pointer_dicts_rejects_extra_change(self) -> None:
		prev = {"a": 1, "ptr": ""}
		curr = {"a": 2, "ptr": "NEW"}
		self.assertFalse(only_supersede_pointer_dicts(prev, curr, pointer="ptr"))

	def test_p127_only_supersede_pointer_dicts_prev_already_set(self) -> None:
		prev = {"a": 1, "ptr": "OLD"}
		curr = {"a": 1, "ptr": "NEW"}
		self.assertFalse(only_supersede_pointer_dicts(prev, curr, pointer="ptr"))


class TestImmutabilityGuardsIntegrationP127(
	_TM2BidSubmissionP115FixtureMixin, _ReleaseProcurementPackageHandoffFixtures
):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		self._supplier_names: list[str] = []

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		for row in frappe.get_all(
			"TM2 Bid Receipt",
			filters={"tender_code": ["like", "TND-P127%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Receipt", row):
				frappe.delete_doc("TM2 Bid Receipt", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Bid Submission",
			filters={"tender_code": ["like", "TND-P127%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Bid Submission", row):
				frappe.delete_doc("TM2 Bid Submission", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Supplier Participation",
			filters={"tender_code": ["like", "TND-P127%"]},
			pluck="name",
		):
			if frappe.db.exists("TM2 Supplier Participation", row):
				frappe.delete_doc("TM2 Supplier Participation", row, force=True, ignore_permissions=True)
		for row in frappe.get_all(
			"TM2 Tender Timeline", filters={"tender_code": ["like", "TND-P127%"]}, pluck="name"
		):
			if frappe.db.exists("TM2 Tender Timeline", row):
				frappe.delete_doc("TM2 Tender Timeline", row, force=True, ignore_permissions=True)
		for row in frappe.get_all("TM2 Tender", filters={"tender_code": ["like", "TND-P127%"]}, pluck="name"):
			if frappe.db.exists("TM2 Tender", row):
				frappe.delete_doc("TM2 Tender", row, force=True, ignore_permissions=True)
		super().tearDown()

	def _receipt_payload(self, bid_name: str, **kwargs) -> dict:
		base = {
			"doctype": "TM2 Bid Receipt",
			"tm2_bid_submission": bid_name,
			"receipt_payload": {"event": "bid_submitted"},
		}
		base.update(kwargs)
		return base

	def test_p127_bid_receipt_uses_shared_immutable_guard(self) -> None:
		tm2, sup = self._fixture_published_with_timeline(tender_code="TND-P127-2028-0001")
		b = frappe.get_doc(self._bid_payload(tm2.name, sup, dsm_output_code="DSM-P127-01")).insert(
			ignore_permissions=True
		)
		r = frappe.get_doc(self._receipt_payload(b.name)).insert(ignore_permissions=True)
		r.reload()
		r.receipt_hash = "TAMPER"
		with self.assertRaises(frappe.ValidationError):
			r.save(ignore_permissions=True)
