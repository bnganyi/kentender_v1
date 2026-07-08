# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0900 — downstream output contracts."""

from __future__ import annotations

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
from kentender_procurement.tender_management.std_instance.downstream import (
	MANUAL_RULE_INJECTION_CODE,
	StdDownstreamConsumptionService,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)


class TestStdInstDownstream0900(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "STDINST-0900 Test Tender"
		doc.tender_reference = "STDINST0900-REF"
		doc.insert(ignore_permissions=True)
		return doc.name

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
				frappe.delete_doc("Tender STD Generated Output", out_name, force=True, ignore_permissions=True)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc("Tender STD Instance BOQ", boq_name, force=True, ignore_permissions=True)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _publish_output(self, instance_name: str, output_type: str) -> str:
		method = {
			"Bundle": StdInstanceGeneratedOutputService.generate_bundle,
			"DSM": StdInstanceGeneratedOutputService.generate_dsm,
			"DOM": StdInstanceGeneratedOutputService.generate_dom,
			"DEM": StdInstanceGeneratedOutputService.generate_dem,
			"DCM": StdInstanceGeneratedOutputService.generate_dcm,
		}[output_type]
		doc = method(instance_name)
		doc = StdInstanceGeneratedOutputService.publish_output(doc.name)
		return doc.name

	def test_std_inst_0900_get_current_outputs_resolve(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			bundle = self._publish_output(si.name, "Bundle")
			dsm = self._publish_output(si.name, "DSM")
			dom = self._publish_output(si.name, "DOM")
			dem = self._publish_output(si.name, "DEM")
			dcm = self._publish_output(si.name, "DCM")

			self.assertEqual(StdDownstreamConsumptionService.get_current_bundle(si.name)["output_code"], bundle)
			self.assertEqual(StdDownstreamConsumptionService.get_current_dsm(si.name)["output_code"], dsm)
			self.assertEqual(StdDownstreamConsumptionService.get_current_dom(si.name)["output_code"], dom)
			self.assertEqual(StdDownstreamConsumptionService.get_current_dem(si.name)["output_code"], dem)
			self.assertEqual(StdDownstreamConsumptionService.get_current_dcm(si.name)["output_code"], dcm)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0900_missing_pointer_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			with self.assertRaises(frappe.ValidationError):
				StdDownstreamConsumptionService.get_current_dsm(si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0900_non_consumable_status_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._publish_output(si.name, "DEM")
			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DEM")
			with self.assertRaises(frappe.ValidationError):
				StdDownstreamConsumptionService.get_current_dem(si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0900_type_mismatch_denied(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			dsm = self._publish_output(si.name, "DSM")
			doc = frappe.get_doc("Tender STD Instance", si.name)
			doc.current_dom_output_code = dsm
			doc.save(ignore_permissions=True)

			with self.assertRaises(frappe.ValidationError):
				StdDownstreamConsumptionService.get_current_dom(si.name)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0900_manual_rule_injection_denied(self) -> None:
		with self.assertRaisesRegex(frappe.ValidationError, "must originate from STD outputs"):
			StdDownstreamConsumptionService.deny_manual_rule_injection(context="submission")
		try:
			StdDownstreamConsumptionService.deny_manual_rule_injection()
		except frappe.ValidationError:
			pass
		last = frappe.local.message_log[-1] if frappe.local.message_log else {}
		self.assertEqual(last.get("title"), MANUAL_RULE_INJECTION_CODE)
