# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0400 — ``Tender STD Generated Output`` versioning.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
	  --module kentender_procurement.tender_management.tests.test_std_inst_generated_output_0400
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
from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_TYPES,
	StdInstanceGeneratedOutputService,
	SYNC_GENERATION_JOB_CODE,
)
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags


class TestStdInstGeneratedOutput0400(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		for out_name in frappe.get_all("Tender STD Generated Output", pluck="name"):
			tsi = frappe.db.get_value("Tender STD Generated Output", out_name, "tender_std_instance")
			if tsi and not frappe.db.exists("Tender STD Instance", tsi):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0400 Test Tender"
		doc.tender_reference = "STDINST0400-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def test_std_inst_0400_generate_publish_all_types(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			iname = si.name
			for fn in (
				StdInstanceGeneratedOutputService.generate_bundle,
				StdInstanceGeneratedOutputService.generate_dsm,
				StdInstanceGeneratedOutputService.generate_dom,
				StdInstanceGeneratedOutputService.generate_dem,
				StdInstanceGeneratedOutputService.generate_dcm,
			):
				doc = fn(iname)
				self.assertEqual(doc.output_status, "Draft")
				self.assertEqual(doc.generated_by_job_code, SYNC_GENERATION_JOB_CODE)
				pub = StdInstanceGeneratedOutputService.publish_output(doc.name)
				self.assertEqual(pub.output_status, "Published")
				self.assertTrue(pub.published_at)

			inst = frappe.get_doc("Tender STD Instance", iname)
			bundle_pub = frappe.get_all(
				"Tender STD Generated Output",
				filters={
					"tender_std_instance": iname,
					"output_type": "Bundle",
					"output_status": "Published",
				},
				pluck="name",
				limit=1,
			)
			self.assertEqual(inst.current_bundle_output_code, bundle_pub[0])
			dsm_pub = frappe.get_all(
				"Tender STD Generated Output",
				filters={
					"tender_std_instance": iname,
					"output_type": "DSM",
					"output_status": "Published",
				},
				pluck="name",
				limit=1,
			)
			self.assertEqual(inst.current_dsm_output_code, dsm_pub[0])

			inst = frappe.get_doc("Tender STD Instance", iname)
			flags = parse_outputs_stale_flags(inst)
			for k in OUTPUT_TYPES:
				self.assertNotIn(k, flags)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0400_second_publish_supersedes(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			b1 = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			self.assertEqual(int(b1.version_number), 1)
			StdInstanceGeneratedOutputService.publish_output(b1.name)
			b2 = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			self.assertEqual(int(b2.version_number), 2)
			StdInstanceGeneratedOutputService.publish_output(b2.name)

			old = frappe.get_doc("Tender STD Generated Output", b1.name)
			self.assertEqual(old.output_status, "Superseded")

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(inst.current_bundle_output_code, b2.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0400_draft_content_not_manually_edited(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			doc = frappe.get_doc("Tender STD Generated Output", b.name)
			raw = doc.content_json
			if isinstance(raw, str):
				payload = json.loads(raw) if raw else {}
			else:
				payload = dict(raw or {})
			payload["tampered"] = True
			doc.content_json = payload
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0400_published_immutable(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			b = StdInstanceGeneratedOutputService.generate_bundle(si.name)
			StdInstanceGeneratedOutputService.publish_output(b.name)
			doc = frappe.get_doc("Tender STD Generated Output", b.name)
			raw = doc.content_json
			if isinstance(raw, str):
				payload = json.loads(raw) if raw else {}
			else:
				payload = dict(raw or {})
			payload["tampered"] = True
			doc.content_json = payload
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0400_mark_output_stale(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			d = StdInstanceGeneratedOutputService.generate_dom(si.name)
			StdInstanceGeneratedOutputService.publish_output(d.name)

			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DOM")

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertIsNone(inst.current_dom_output_code)
			self.assertIn("DOM", parse_outputs_stale_flags(inst))

			out = frappe.get_doc("Tender STD Generated Output", d.name)
			self.assertEqual(out.output_status, "Stale")
		finally:
			self._cleanup_tender(tender)
