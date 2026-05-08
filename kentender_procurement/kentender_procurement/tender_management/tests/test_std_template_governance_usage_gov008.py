# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-GOV-008 — eligibility, usage recording, impact, resolve (doc 7 §13.4, §16).

Run::

    bench --site kentender.midas.com run-tests --app kentender_procurement \\
        --module kentender_procurement.tender_management.tests.test_std_template_governance_usage_gov008
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.services import std_template_governance as gov
from kentender_procurement.tender_management.services.std_template_governance_usage import (
	check_std_template_tender_creation_eligibility,
	get_std_template_usage_impact,
	record_std_template_usage,
	resolve_active_std_template_for_context,
)
from kentender_procurement.tender_management.tests.test_std_template_governance_events_gov005 import (
	_new_gov005_std_template,
)


def _package_hash_for(doc_name: str) -> str:
	ph = frappe.db.get_value("STD Template", doc_name, "package_hash")
	assert ph
	return str(ph)


def _set_active_eligible(doc_name: str) -> str:
	ph = _package_hash_for(doc_name)
	frappe.db.set_value(
		"STD Template",
		doc_name,
		{
			"lifecycle_status": gov.STATUS_ACTIVE,
			"allowed_for_tender_creation": 1,
			"package_hash": ph,
			"activation_package_hash": ph,
			"approval_package_hash": ph,
			"latest_validation_package_hash": ph,
			"validation_is_current": 1,
			"is_suspended": 0,
		},
	)
	frappe.db.commit()
	return ph


class TestStdTemplateGovernanceUsageGov008(IntegrationTestCase):
	def setUp(self) -> None:
		frappe.set_user("Administrator")
		self._code = f"GOV008-{frappe.generate_hash(length=10)}"
		self.doc = _new_gov005_std_template(self._code)

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		if frappe.db.exists("STD Template", self._code):
			frappe.db.delete("STD Template Usage", {"parent": self._code})
			frappe.db.set_value(
				"STD Template",
				self._code,
				{
					"tender_usage_count": 0,
					"locked_due_to_usage": 0,
					"mutation_blocked": 0,
				},
			)
			frappe.delete_doc("STD Template", self._code, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_std_gov_008_eligibility_active_ok(self) -> None:
		_set_active_eligible(self._code)
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertTrue(out["eligible"])
		self.assertEqual(out["reasons"], [])

	def test_std_gov_008_eligibility_hash_mismatch(self) -> None:
		_set_active_eligible(self._code)
		frappe.db.set_value("STD Template", self._code, "approval_package_hash", "0" * 64)
		frappe.db.commit()
		out = check_std_template_tender_creation_eligibility(self._code, None)
		self.assertFalse(out["eligible"])
		self.assertTrue(any("hash_mismatch" in r for r in out["reasons"]))

	def test_std_gov_008_eligibility_context_family_mismatch(self) -> None:
		_set_active_eligible(self._code)
		out = check_std_template_tender_creation_eligibility(
			self._code,
			{"template_family": "Goods"},
		)
		self.assertFalse(out["eligible"])
		self.assertIn("template_family_mismatch", out["reasons"])

	def test_std_gov_008_emit_usage_blocked_event(self) -> None:
		frappe.db.set_value(
			"STD Template",
			self._code,
			{"lifecycle_status": gov.STATUS_IMPORTED, "allowed_for_tender_creation": 0},
		)
		frappe.db.commit()
		before = len(frappe.get_doc("STD Template", self._code).lifecycle_events or [])
		check_std_template_tender_creation_eligibility(
			self._code,
			{"emit_usage_blocked_event": True},
		)
		after = len(frappe.get_doc("STD Template", self._code).lifecycle_events or [])
		self.assertEqual(after, before + 1)
		last = (frappe.get_doc("STD Template", self._code).lifecycle_events or [])[-1]
		self.assertEqual(last.event_code, gov.EVT_USAGE_BLOCKED)

	def test_std_gov_008_record_usage_and_lock(self) -> None:
		_set_active_eligible(self._code)
		out = record_std_template_usage(
			self._code,
			"Tender",
			tender="TND-1",
			payload={"k": 1},
		)
		self.assertTrue(out["ok"])
		doc = frappe.get_doc("STD Template", self._code)
		self.assertEqual(int(doc.tender_usage_count), 1)
		self.assertEqual(int(doc.locked_due_to_usage or 0), 1)
		self.assertEqual(int(doc.mutation_blocked or 0), 1)
		self.assertEqual(len(doc.template_usage or []), 1)
		codes = [e.event_code for e in (doc.lifecycle_events or [])]
		self.assertIn(gov.EVT_USED_FOR_TENDER, codes)

	def test_std_gov_008_record_usage_rejects_ineligible(self) -> None:
		frappe.db.set_value("STD Template", self._code, "lifecycle_status", gov.STATUS_APPROVED)
		frappe.db.commit()
		with self.assertRaises(frappe.ValidationError):
			record_std_template_usage(self._code, "Tender")

	def test_std_gov_008_get_usage_impact(self) -> None:
		_set_active_eligible(self._code)
		record_std_template_usage(self._code, "Planning Mapping Test")
		imp = get_std_template_usage_impact(self._code)
		self.assertEqual(imp["usage_row_count"], 1)
		self.assertEqual(imp["tender_usage_count"], 1)
		self.assertIsNotNone(imp.get("last_usage_row"))

	def test_std_gov_008_resolve_active_unique(self) -> None:
		_set_active_eligible(self._code)
		out = resolve_active_std_template_for_context(
			{"template_family": "Works", "procurement_category": "WORKS", "template_code": self._code}
		)
		self.assertTrue(out["ok"])
		self.assertEqual(out["std_template"], self._code)

	def test_std_gov_008_resolve_ambiguous(self) -> None:
		other = f"GOV008B-{frappe.generate_hash(length=8)}"
		try:
			_new_gov005_std_template(other)
			_set_active_eligible(self._code)
			_set_active_eligible(other)
			out = resolve_active_std_template_for_context(
				{"template_family": "Works", "procurement_category": "WORKS"}
			)
			self.assertFalse(out["ok"])
			self.assertEqual(out["error"], "ambiguous")
			self.assertGreaterEqual(len(out.get("candidates") or []), 2)
		finally:
			if frappe.db.exists("STD Template", other):
				frappe.delete_doc("STD Template", other, force=True, ignore_permissions=True)
				frappe.db.commit()

	def test_std_gov_008_resolve_not_found(self) -> None:
		out = resolve_active_std_template_for_context(
			{"template_family": "Works", "procurement_category": "ZZZ_NOPE"}
		)
		self.assertFalse(out["ok"])
		self.assertEqual(out["error"], "not_found")

	def test_std_gov_008_guest_cannot_record_usage(self) -> None:
		_set_active_eligible(self._code)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			record_std_template_usage(self._code, "Tender")
