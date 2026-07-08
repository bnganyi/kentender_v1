# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0200 — WorksTdsCompletionService TDS parameter completion.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_works_comp_tds_completion_0200
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
	_normalize_pc,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.works_completion.services.tds_completion import (
	WorksTdsCompletionService,
)


def _full_tds_payload(**overrides: object) -> dict[str, object]:
	"""Minimal consistent TDS dict covering validation rules (single-call save)."""
	base: dict[str, object] = {
		"tender_title": "WORKS-COMP-0200 Tender",
		"procuring_entity_name": "PE Name",
		"project_location": "Nairobi",
		"procurement_method": "Open National",
		"submission_deadline": "2026-08-15 17:00:00",
		"opening_datetime": "2026-08-16 09:00:00",
		"clarification_deadline": "2026-08-10 12:00:00",
		"bid_validity_days": "120",
		"tender_security_required": "0",
		"tender_security_type": "",
		"tender_security_amount": "",
		"tender_security_currency": "",
		"site_visit_required": "0",
		"site_visit_datetime": "",
		"site_visit_location": "",
		"pre_tender_meeting_required": "0",
		"pre_tender_meeting_datetime": "",
		"pre_tender_meeting_location": "",
		"bid_currency": "KES",
		"language": "en",
		"margin_of_preference_applicable": "0",
	}
	base.update(overrides)
	return base


class TestWorksCompTdsCompletion0200(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tm2_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "WORKS-COMP-0200 Test Tender"
		doc.tender_reference = "WORKSCOMP0200-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _delete_std_instances_for_tender(self, tender: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender},
			pluck="name",
		):
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)

	def _delete_tender(self, name: str) -> None:
		if frappe.db.exists("TM2 Tender", name):
			self._delete_std_instances_for_tender(name)
			frappe.delete_doc("TM2 Tender", name, force=True, ignore_permissions=True)

	def _codes(self, out: dict) -> list[str]:
		return [b["code"] for b in out.get("blockers") or []]

	def test_works_comp_0200_opening_before_submission_invalid(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			bad = _full_tds_payload(
				submission_deadline="2026-08-15 17:00:00",
				opening_datetime="2026-08-14 09:00:00",
			)
			out = WorksTdsCompletionService.validate_tds_values(si.name, prospective_values=bad)
			self.assertFalse(out["valid"], out)
			self.assertIn("TDS_OPENING_DATETIME_INVALID", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0200_security_required_missing_amount(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			bad = _full_tds_payload(
				tender_security_required="1",
				tender_security_type="Bid Bond",
				tender_security_amount="",
				tender_security_currency="USD",
			)
			out = WorksTdsCompletionService.validate_tds_values(si.name, prospective_values=bad)
			self.assertFalse(out["valid"], out)
			self.assertIn("TENDER_SECURITY_AMOUNT_MISSING", self._codes(out))
		finally:
			self._delete_tender(tender)

	def test_works_comp_0200_save_valid_then_validate_ok(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			payload = _full_tds_payload()
			WorksTdsCompletionService.save_tds_values(si.name, payload)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			pcs = {_normalize_pc(r.parameter_code) for r in (doc.parameter_values or [])}
			for key in (
				"submission_deadline",
				"opening_datetime",
				"tender_title",
				"bid_validity_days",
			):
				self.assertIn(key, pcs)
			after = WorksTdsCompletionService.validate_tds_values(si.name)
			self.assertTrue(after["valid"], after)
			self.assertEqual(after.get("blockers"), [])
		finally:
			self._delete_tender(tender)

	def test_works_comp_0200_security_amount_change_marks_stale_bundle_dsm_dem(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksTdsCompletionService.save_tds_values(
				si.name,
				_full_tds_payload(
					tender_security_required="1",
					tender_security_type="Bid Bond",
					tender_security_amount="100000",
					tender_security_currency="KES",
				),
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.current_bundle_output_code = "BUNDLE-0200"
			doc.current_dsm_output_code = "DSM-0200"
			doc.current_dem_output_code = "DEM-0200"
			doc.save(ignore_permissions=True)

			WorksTdsCompletionService.save_tds_values(
				si.name,
				{"tender_security_amount": "150000"},
			)
			doc = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(doc)
			self.assertIn("Bundle", flags)
			self.assertIn("DSM", flags)
			self.assertIn("DEM", flags)
			raw = (doc.outputs_stale_flags or "").strip()
			parsed = json.loads(raw)
			self.assertIsInstance(parsed, list)
		finally:
			self._delete_tender(tender)

	def test_works_comp_0200_save_rejects_invalid_patch(self) -> None:
		tender = self._minimal_tm2_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksTdsCompletionService.save_tds_values(si.name, _full_tds_payload())
			with self.assertRaises(frappe.ValidationError):
				WorksTdsCompletionService.save_tds_values(
					si.name,
					{
						"opening_datetime": "2026-01-01 09:00:00",
						"submission_deadline": "2026-12-31 17:00:00",
					},
				)
		finally:
			self._delete_tender(tender)
