# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Integration: electronic bid draft → validate → seal → immutable receipt."""

from __future__ import annotations

import unittest

import frappe

from kentender_procurement.tender_configurations.seed.e1_nssf_seed import (
	CONFIG_REF,
	seed_e1_nssf_tender_configuration,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	create_or_get_draft,
	fill_draft_for_tests,
	get_receipt,
	save_section_responses,
	submit_and_seal,
	validate_submission,
)


class TestElectronicBidSubmission(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe.set_user("Administrator")
		cls.seed = seed_e1_nssf_tender_configuration(clear=True)
		cls.cfg_id = cls.seed["configuration_id"]

	def test_draft_validate_seal_immutable(self):
		draft = create_or_get_draft(self.cfg_id, "PoC Demo Bidder")
		bid_id = draft["bid_id"]
		self.assertEqual(draft["status"], "Draft")

		empty = validate_submission(bid_id)
		self.assertFalse(empty["ok"])
		self.assertGreater(empty["error_count"], 0)

		filled = fill_draft_for_tests(bid_id)
		self.assertIn("technical_compliance_matrix", filled["responses"])
		self.assertEqual(len(filled["responses"]["technical_compliance_matrix"]), 190)

		ok = validate_submission(bid_id)
		self.assertTrue(ok["ok"], ok.get("errors")[:3] if ok.get("errors") else ok)

		receipt = submit_and_seal(bid_id)
		self.assertTrue(receipt.get("receipt_code", "").startswith("EBD-"))
		self.assertTrue(receipt.get("seal_hash"))

		again = get_receipt(bid_id)
		self.assertEqual(again["receipt_code"], receipt["receipt_code"])

		with self.assertRaises(Exception):
			save_section_responses(
				bid_id,
				"form_of_tender",
				{"company_name": "Should fail"},
			)

	def test_admin_gate(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(Exception):
				create_or_get_draft(CONFIG_REF)
		finally:
			frappe.set_user("Administrator")
