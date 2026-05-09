# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0110 — WorksContextValidator.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_context_validator_0110
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)


class TestWorksCompContextValidator0110(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_procurement_tender(self, **kwargs) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0110 Test Tender"
		doc.tender_reference = "WORKSCOMP0110-REF"
		for k, v in kwargs.items():
			doc.set(k, v)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("Procurement Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("Procurement Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def test_works_comp_0110_not_found(self) -> None:
		out = validate_works_completion_context("NONEXISTENT-STDINST-WORKSCOMP0110")
		self.assertFalse(out["valid"])
		self.assertIn("WORKS_INSTANCE_NOT_FOUND", self._codes(out))

	def test_works_comp_0110_valid_works_instance(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = validate_works_completion_context(si.name)
			self.assertTrue(out["valid"], out)
			self.assertEqual(out.get("blockers"), [])
		finally:
			self._delete_tender(tender)

	def test_works_comp_0110_category_invalid(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", si.name, "procurement_category", "GOODS")
			out = validate_works_completion_context(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_CATEGORY_INVALID", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0110_boq_required_by_profile(self) -> None:
		tender = self._minimal_procurement_tender(
			configuration_json=json.dumps({"WORKS.BOQ_REQUIRED": True}, sort_keys=True),
		)
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", si.name, "procurement_category", "GOODS")
			out = validate_works_completion_context(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_BOQ_REQUIRED_BY_PROFILE", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0110_instance_locked(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", si.name, "instance_status", "Published Locked")
			out = validate_works_completion_context(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_INSTANCE_LOCKED", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0110_template_lineage_mismatch(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value(
				"Tender STD Instance",
				si.name,
				"template_version_code",
				"definitely-not-bound-version-0110",
			)
			out = validate_works_completion_context(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_TEMPLATE_LINEAGE_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0110_profile_fields_missing(self) -> None:
		tender = self._minimal_procurement_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.db.set_value("Tender STD Instance", si.name, "applicability_profile_code", "")
			out = validate_works_completion_context(si.name)
			self.assertFalse(out["valid"])
			self.assertIn("WORKS_PROFILE_INVALID", self._codes(out))
		finally:
			self._delete_tender(tender)
