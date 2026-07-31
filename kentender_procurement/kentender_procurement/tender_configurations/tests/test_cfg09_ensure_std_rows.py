# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Run Check must materialize STD-bound rows and bind legacy orphans."""

from __future__ import annotations

import json
import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from kentender_procurement.tender_configurations.services.contract_parameter_readiness import (
	ensure_std_declared_contract_values,
	readiness_blockers_for_doc,
)
from kentender_procurement.tender_configurations.services.contract_values import (
	save_configuration_contract_values,
)

CANONICAL = "KE-PPRA-IT-2022-04"


class TestCfg09EnsureStdRows(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("STD Parameter", {"package_id": CANONICAL}):
			self.skipTest("Canonical IT STD package not loaded")
		# Prefer the journey IP config when present.
		if frappe.db.exists("Tender Configuration", "TCFG-JOURNEY-CFG-IP"):
			self.cfg_id = "TCFG-JOURNEY-CFG-IP"
		else:
			self.skipTest("Journey IP configuration not present")

	def test_ensure_binds_legacy_orphans_and_adds_payment(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		existing = json.loads(doc.contract_values or "{}").get("contract_values") or []
		merged = ensure_std_declared_contract_values(doc, existing)
		by_label = { (r.get("item_label") or "").lower(): r for r in merged }
		# Legacy Performance Security / Warranty period must receive STD bindings.
		perf = by_label.get("performance security")
		self.assertIsNotNone(perf)
		self.assertEqual(perf.get("parameter_code"), "IT-SCC-029")
		self.assertEqual(perf.get("readiness_parameter_id"), "performance_security")
		warranty = by_label.get("warranty period") or by_label.get(
			"warranty period and excluded/included support services"
		)
		# Either rebound orphan or STD-titled draft.
		bound_warranty = [
			r
			for r in merged
			if r.get("readiness_parameter_id") == "warranty" or r.get("parameter_code") == "IT-SCC-053"
		]
		self.assertTrue(bound_warranty)
		# Payment must appear as a visible STD-bound row.
		payment_rows = [
			r
			for r in merged
			if r.get("readiness_parameter_id") == "payment" or r.get("parameter_code") == "IT-SCC-014"
		]
		self.assertTrue(payment_rows, "Payment schedule (IT-SCC-014) must be in the table")
		# Must not re-invent pack samples.
		labels = {r.get("item_label") for r in merged}
		# Existing orphan Data Residency may remain, but ensure must not add a new unbound invented one
		# if it wasn't already there — if present it stays unbound.
		self.assertFalse(
			any(
				r.get("item_label") == "Data Residency" and r.get("parameter_code")
				for r in merged
			)
		)

	def test_run_check_clears_perf_and_warranty_blockers_for_journey_ip(self):
		doc = frappe.get_doc("Tender Configuration", self.cfg_id)
		existing = json.loads(doc.contract_values or "{}").get("contract_values") or []
		out = save_configuration_contract_values(
			self.cfg_id,
			{"contract_values": existing, "hydrate": 1},
		)
		messages = [b.get("message") for b in out.get("blockers") or []]
		self.assertNotIn("Performance security value is missing.", messages)
		self.assertNotIn("Warranty value is missing.", messages)
		# Payment may still block until the PE enters a value — but the row must exist.
		payment = [
			r
			for r in out["contract_values"]
			if r.get("parameter_code") == "IT-SCC-014" or r.get("readiness_parameter_id") == "payment"
		]
		self.assertTrue(payment)
		if "Payment schedule value is missing." in messages:
			self.assertFalse(
				(payment[0].get("value_or_obligation") or "").strip()
				or payment[0].get("not_applicable")
			)


class TestCfg09EnsureUnit(unittest.TestCase):
	def test_legacy_bind_and_add_payment_without_db(self):
		from kentender_procurement.tender_configurations.services import (
			contract_parameter_readiness as mod,
		)

		class _Doc:
			std_version = CANONICAL
			implementation_schedule = None

		# Stub STD presence so drafts are generated without a live DB package.
		original_codes = mod._std_codes_present
		original_titles = mod._std_parameter_titles_by_code
		mod._std_codes_present = lambda _v: {
			"IT-SCC-011",
			"IT-SCC-014",
			"IT-SCC-029",
			"IT-SCC-053",
		}
		mod._std_parameter_titles_by_code = lambda _v: {
			"IT-SCC-014": "Payment schedule category model",
			"IT-SCC-029": "Performance security percentage",
			"IT-SCC-053": "Warranty period and excluded/included support services",
			"IT-SCC-011": "Commencement period after effective date",
		}
		try:
			existing = [
				{
					"item_label": "Performance Security",
					"not_applicable": 1,
					"not_applicable_reason": "Not required",
				},
				{
					"item_label": "Warranty period",
					"value_or_obligation": "12 months",
				},
				{"item_label": "Data Residency", "value_or_obligation": "invented"},
			]
			merged = ensure_std_declared_contract_values(_Doc(), existing)
			perf = next(r for r in merged if r["item_label"] == "Performance Security")
			self.assertEqual(perf["parameter_code"], "IT-SCC-029")
			self.assertEqual(perf["not_applicable"], 1)
			warr = next(r for r in merged if r["item_label"] == "Warranty period")
			self.assertEqual(warr["parameter_code"], "IT-SCC-053")
			self.assertEqual(warr["value_or_obligation"], "12 months")
			self.assertTrue(
				any(r.get("parameter_code") == "IT-SCC-014" for r in merged)
			)
			# Data Residency stays as orphan user data — not STD-bound by ensure.
			dr = next(r for r in merged if r["item_label"] == "Data Residency")
			self.assertFalse(dr.get("parameter_code"))
		finally:
			mod._std_codes_present = original_codes
			mod._std_parameter_titles_by_code = original_titles


if __name__ == "__main__":
	unittest.main()
