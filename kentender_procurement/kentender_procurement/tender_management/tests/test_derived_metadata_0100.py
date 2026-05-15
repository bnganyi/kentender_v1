# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0100 — common generated output metadata.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_metadata_0100
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.tender_management.derived_models.common import metadata as derived_metadata
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_STATUSES,
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
)


class TestDerivedMetadata0100(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def test_derived_0100_enums_match_service_constants(self) -> None:
		self.assertEqual(derived_metadata.OUTPUT_TYPES, OUTPUT_TYPES)
		self.assertEqual(derived_metadata.OUTPUT_STATUSES, OUTPUT_STATUSES)

	def test_derived_0100_validate_output_type_status(self) -> None:
		self.assertEqual(derived_metadata.validate_output_type("Bundle"), "Bundle")
		with self.assertRaises(frappe.ValidationError):
			derived_metadata.validate_output_type("InvalidType")
		self.assertEqual(derived_metadata.validate_output_status("Current"), "Current")
		with self.assertRaises(frappe.ValidationError):
			derived_metadata.validate_output_status("NotAStatus")

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0100 Test Tender"
		doc.tender_reference = "DERIVED0100-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for snap in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance Snapshot",
					snap,
					force=True,
					ignore_permissions=True,
				)
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0100_tender_code_on_generate_and_supersedes_on_second_publish(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			b1 = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			self.assertEqual((b1.tender_code or "").strip(), "DERIVED0100-REF")
			pub1 = StdInstanceGeneratedOutputService.publish_output(b1.name)
			self.assertFalse((pub1.supersedes_output_code or "").strip())

			b2 = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			self.assertEqual((b2.tender_code or "").strip(), "DERIVED0100-REF")
			pub2 = StdInstanceGeneratedOutputService.publish_output(b2.name)
			self.assertEqual((pub2.supersedes_output_code or "").strip(), b1.name)

			old = frappe.get_doc("Tender STD Generated Output", b1.name)
			self.assertEqual(old.output_status, "Superseded")
		finally:
			self._cleanup_tender(tender)

	def test_derived_0100_single_current_per_instance_type(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			d1 = StdInstanceGeneratedOutputService.generate_dom(si.name)
			d2 = StdInstanceGeneratedOutputService.generate_dom(si.name)
			d1.flags.allow_generated_output_service_mutation = True
			d1.output_status = "Current"
			d1.save(ignore_permissions=True)

			d2.flags.allow_generated_output_service_mutation = True
			d2.output_status = "Current"
			with self.assertRaises(frappe.ValidationError):
				d2.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_derived_0100_snapshot_bound_output_blocks_content_tamper(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			snap = frappe.new_doc("Tender STD Instance Snapshot")
			snap.tender_std_instance = si.name
			snap.procurement_tender = tender
			snap.snapshot_type = "Configuration"
			snap.snapshot_reason = "DERIVED-0100 test snapshot"
			snap.snapshot_status = "Final"
			snap.source_template_version_code = inst.template_version_code or "TV"
			snap.parameter_values_hash = "pv"
			snap.works_requirements_hash = "wr"
			snap.attachments_hash = "at"
			snap.boq_hash = "bq"
			snap.complete_instance_hash = "ci"
			snap.created_by = frappe.session.user
			snap.created_at = now_datetime()
			snap.insert(ignore_permissions=True)

			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			doc = frappe.get_doc("Tender STD Generated Output", b.name)
			doc.flags.allow_generated_output_service_mutation = True
			doc.source_instance_snapshot_code = snap.name
			doc.save(ignore_permissions=True)

			doc2 = frappe.get_doc("Tender STD Generated Output", b.name)
			raw = doc2.content_json
			if isinstance(raw, str):
				payload = json.loads(raw) if raw else {}
			else:
				payload = dict(raw or {})
			payload["tampered"] = True
			doc2.content_json = payload
			with self.assertRaises(frappe.ValidationError):
				doc2.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)
