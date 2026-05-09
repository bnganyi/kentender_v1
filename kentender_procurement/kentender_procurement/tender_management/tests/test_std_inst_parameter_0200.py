# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0200 — parameter values child table and ``StdInstanceParameterService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_parameter_0200
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
from kentender_procurement.tender_management.std_instance.parameter import (
	parse_outputs_stale_flags,
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.state import StdInstanceStateService


class TestStdInstParameter0200(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0200 Test Tender"
		doc.tender_reference = "STDINST0200-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"procurement_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0200_set_and_upsert_parameter(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			StdInstanceParameterService.set_parameter_value(
				name,
				"lot_threshold",
				"5",
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			self.assertEqual(len(doc.parameter_values), 1)
			self.assertEqual(doc.parameter_values[0].parameter_code, "lot_threshold")
			self.assertEqual(doc.parameter_values[0].value, "5")
			self.assertEqual(doc.parameter_values[0].value_status, "Provided")

			StdInstanceParameterService.set_parameter_value(
				name,
				"lot_threshold",
				"9",
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			self.assertEqual(len(doc.parameter_values), 1)
			self.assertEqual(doc.parameter_values[0].value, "9")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0200_validate_missing(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"optional_flag",
				"",
				ignore_publication_lock=False,
			)
			out = StdInstanceParameterService.validate_parameter_values(si.name)
			self.assertFalse(out["ok"])
			self.assertIn("optional_flag", out["missing"])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0200_lock_then_set_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceParameterService.set_parameter_value(
				si.name,
				"x_code",
				"1",
				ignore_publication_lock=False,
			)
			StdInstanceParameterService.lock_parameter_values(si.name)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceParameterService.set_parameter_value(
					si.name,
					"x_code",
					"2",
					ignore_publication_lock=False,
				)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0200_publication_locked_denies_set(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			for target in (
				"In Configuration",
				"Ready for Publication",
				"Locked for Approval",
				"Published Locked",
			):
				si = StdInstanceStateService.apply_transition(name, target, ignore_permissions=True)
				name = si.name

			with self.assertRaises(frappe.ValidationError):
				StdInstanceParameterService.set_parameter_value(
					name,
					"after_pub",
					"v",
					ignore_publication_lock=False,
				)

			StdInstanceParameterService.set_parameter_value(
				name,
				"bypass",
				"v",
				ignore_publication_lock=True,
				ignore_row_lock=True,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			self.assertTrue(any(r.parameter_code == "bypass" for r in doc.parameter_values))
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0200_submission_deadline_marks_stale_and_blocked(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			name = si.name
			doc = frappe.get_doc("Tender STD Instance", name)
			doc.readiness_status = "Ready"
			doc.current_bundle_output_code = "BUNDLE-1"
			doc.current_dsm_output_code = "DSM-1"
			doc.current_dom_output_code = "DOM-1"
			doc.save(ignore_permissions=True)

			StdInstanceParameterService.set_parameter_value(
				name,
				"submission_deadline",
				"2026-12-31",
				ignore_publication_lock=False,
			)
			doc = frappe.get_doc("Tender STD Instance", name)
			flags = parse_outputs_stale_flags(doc)
			self.assertIn("Bundle", flags)
			self.assertIn("DSM", flags)
			self.assertIn("DOM", flags)
			self.assertEqual(doc.readiness_status, "Blocked")
			self.assertIsNone(doc.current_bundle_output_code)
			self.assertIsNone(doc.current_dsm_output_code)
			self.assertIsNone(doc.current_dom_output_code)
			raw = (doc.outputs_stale_flags or "").strip()
			parsed = json.loads(raw)
			self.assertIsInstance(parsed, list)
		finally:
			self._cleanup_tender(tender)
