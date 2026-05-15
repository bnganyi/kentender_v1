# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0120 — DerivedOutputVersioningService.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_versioning_0120
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.tender_management.derived_models.common.versioning import (
	DERIVED_OUTPUT_VERSIONING_TITLE,
	DerivedOutputVersioningService,
)
from kentender_procurement.tender_management.derived_models.dsm.schema import (
	dsm_default_boq_rate_entry,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


def _minimal_dsm_content(std_inst: str) -> dict:
	tr = {"source_type": "SystemRule"}
	return {
		"std_inst": std_inst,
		"output_type": "DSM",
		"requirements": [
			{
				"requirement_code": "T-REQ-1",
				"requirement_type": "Form",
				"label": "T",
				"mandatory": True,
				"supplier_action": "CompleteForm",
				"source_trace": tr,
			},
		],
		"boq_rate_entry": dsm_default_boq_rate_entry(enabled=False),
		"addendum_acknowledgements": [],
	}


def _minimal_valid_boq_payload() -> dict:
	return {
		"header": {"currency": "USD"},
		"bills": [
			{
				"bill_number": "B1",
				"bill_title": "Preliminaries",
				"bill_type": "Standard",
				"order_index": 0,
				"items": [
					{
						"item_number": "1.1",
						"description": "Site clearance",
						"unit": "m2",
						"quantity": 100,
						"item_type": "Normal",
						"supplier_input_mode": "Rate Only",
					},
				],
			},
		],
	}


class TestDerivedVersioning0120(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		frappe.clear_messages()
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			for snap_name in frappe.get_all(
				"Tender STD Instance Snapshot",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance Snapshot", snap_name, force=True, ignore_permissions=True)
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
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def test_derived_0120_create_draft_increments_version(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Draft"
		doc.tender_reference = "DERIVED0120-DRAFT"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p1 = _minimal_dsm_content(si.name)
			d1 = DerivedOutputVersioningService.createDraftOutput(
				si.name,
				"DSM",
				p1,
				{"generated_by_job_code": "TEST-DERIVED-0120"},
			)
			self.assertEqual(d1.output_status, "Draft")
			self.assertEqual(int(d1.version_number or 0), 1)
			self.assertEqual((d1.generated_by_job_code or "").strip(), "TEST-DERIVED-0120")

			d2 = DerivedOutputVersioningService.createDraftOutput(si.name, "DSM", p1)
			self.assertEqual(int(d2.version_number or 0), 2)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_mark_current_second_draft_fails(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Current"
		doc.tender_reference = "DERIVED0120-CUR"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			p = _minimal_dsm_content(si.name)
			d1 = DerivedOutputVersioningService.createDraftOutput(si.name, "DSM", p)
			d2 = DerivedOutputVersioningService.createDraftOutput(si.name, "DSM", p)
			DerivedOutputVersioningService.markCurrent(d1.name)
			with self.assertRaises(frappe.ValidationError):
				DerivedOutputVersioningService.markCurrent(d2.name)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_mark_published_sets_snapshot_code(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Snap"
		doc.tender_reference = "DERIVED0120-SNAP"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			inst = frappe.get_doc("Tender STD Instance", si.name)
			snap = frappe.new_doc("Tender STD Instance Snapshot")
			snap.tender_std_instance = si.name
			snap.procurement_tender = doc.name
			snap.snapshot_type = "Configuration"
			snap.snapshot_reason = "DERIVED-0120"
			snap.snapshot_status = "Draft"
			snap.source_template_version_code = inst.template_version_code or "TV"
			snap.parameter_values_hash = "pv"
			snap.works_requirements_hash = "wr"
			snap.attachments_hash = "at"
			snap.boq_hash = "bq"
			snap.complete_instance_hash = "ci"
			snap.created_by = frappe.session.user
			snap.created_at = now_datetime()
			snap.insert(ignore_permissions=True)

			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			pub = DerivedOutputVersioningService.markPublished(dsm.name, snapshot_code=snap.name)
			self.assertEqual(pub.output_status, "Published")
			self.assertEqual((pub.source_instance_snapshot_code or "").strip(), snap.name)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_mark_stale_blocks_readiness_flags(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Stale"
		doc.tender_reference = "DERIVED0120-STALE"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_valid_boq_payload())
			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			pub = StdInstanceGeneratedOutputService.publish_output(b.name)
			self.assertTrue((pub.name or "").strip())

			DerivedOutputVersioningService.markStale(pub.name, reason="test-regenerate")
			inst = frappe.get_doc("Tender STD Instance", si.name)
			flags = parse_outputs_stale_flags(inst)
			self.assertIn("Bundle", flags)

			ev = StdInstanceReadinessService.evaluate(si.name, persist=False, emit_audit=False)
			codes = [x.get("code") for x in (ev.get("blockers") or [])]
			self.assertIn("STALE_OUTPUTS_PRESENT", codes)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_supersede_output_and_clears_pointer(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Super"
		doc.tender_reference = "DERIVED0120-SUP"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_valid_boq_payload())
			dsm1 = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			pub1 = StdInstanceGeneratedOutputService.publish_output(dsm1.name)
			dsm2 = StdInstanceGeneratedOutputService.generate_dsm(si.name)

			DerivedOutputVersioningService.supersedeOutput(pub1.name, dsm2.name)

			old = frappe.get_doc("Tender STD Generated Output", pub1.name)
			self.assertEqual(old.output_status, "Superseded")
			new = frappe.get_doc("Tender STD Generated Output", dsm2.name)
			self.assertEqual((new.supersedes_output_code or "").strip(), pub1.name)

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertFalse((inst.current_dsm_output_code or "").strip())
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_get_current_and_get_version(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Get"
		doc.tender_reference = "DERIVED0120-GET"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, _minimal_valid_boq_payload())
			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			pub = StdInstanceGeneratedOutputService.publish_output(b.name)

			cur = DerivedOutputVersioningService.getCurrentOutput(si.name, "Bundle")
			self.assertEqual(cur["name"], pub.name)
			self.assertEqual(cur["output_status"], "Published")
			self.assertIn("content_json", cur)

			ver = DerivedOutputVersioningService.getOutputVersion(pub.name)
			self.assertEqual(ver["name"], pub.name)
			self.assertEqual(ver["output_type"], "Bundle")
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0120_get_current_raises_when_missing(self) -> None:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0120 Missing"
		doc.tender_reference = "DERIVED0120-MISS"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				DerivedOutputVersioningService.getCurrentOutput(si.name, "Bundle")
			self.assertEqual(_last_msg_title(), DERIVED_OUTPUT_VERSIONING_TITLE)
		finally:
			self._cleanup_tender(doc.name)
