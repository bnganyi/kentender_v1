# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0700 — readiness evaluation service."""

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
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)


class TestStdInstReadiness0700(IntegrationTestCase):
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
		doc.tender_title = "STDINST-0700 Test Tender"
		doc.tender_reference = "STDINST0700-REF"
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

	def _publish_all_outputs(self, instance_name: str) -> None:
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(instance_name)
			StdInstanceGeneratedOutputService.publish_output(out.name)

	def _ensure_minimum_boq(self, instance_name: str) -> None:
		boq = StdInstanceBoqService.create_boq_for_instance(
			instance_name,
			ignore_boq_publication_lock=True,
		)
		boq = StdInstanceBoqService.add_bill(
			boq.name,
			"1",
			"General",
			"Works",
			ignore_boq_publication_lock=True,
		)
		bill_code = (boq.boq_bills or [])[0].bill_instance_code
		StdInstanceBoqService.add_item(
			boq.name,
			bill_code,
			"1.1",
			"Site mobilization",
			"Item",
			1,
			ignore_boq_publication_lock=True,
		)

	def test_std_inst_0700_blocked_when_outputs_missing(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out = StdInstanceReadinessService.evaluate(si.name)
			self.assertEqual(out["status"], "Blocked")
			codes = [b["code"] for b in out["blockers"]]
			for code in ("BUNDLE_MISSING", "DSM_MISSING", "DOM_MISSING", "DEM_MISSING", "DCM_MISSING"):
				self.assertIn(code, codes)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0700_blocked_when_stale_outputs_present(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._publish_all_outputs(si.name)
			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DOM")

			out = StdInstanceReadinessService.evaluate(si.name)
			self.assertEqual(out["status"], "Blocked")
			codes = [b["code"] for b in out["blockers"]]
			self.assertIn("STALE_OUTPUTS_PRESENT", codes)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0700_blocked_when_parameter_and_works_invalid(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceParameterService.set_parameter_value(si.name, "submission_deadline", None)
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"SPEC-1",
				requirement_status="Missing",
				structured_text="",
				attachment_required=True,
				attachment_status="Missing",
			)
			out = StdInstanceReadinessService.evaluate(si.name)
			codes = [b["code"] for b in out["blockers"]]
			self.assertIn("PARAMETERS_INCOMPLETE", codes)
			self.assertIn("WORKS_REQUIREMENTS_INCOMPLETE", codes)
			self.assertIn("REQUIRED_ATTACHMENTS_INCOMPLETE", codes)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0700_ready_when_inputs_and_outputs_current(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			StdInstanceParameterService.set_parameter_value(si.name, "submission_deadline", "2026-12-31")
			StdInstanceWorksRequirementService.set_works_requirement(
				si.name,
				"SPEC-READY",
				requirement_status="Complete",
				structured_text="Specification baseline",
				attachment_required=False,
				attachment_status="Not Required",
			)
			self._ensure_minimum_boq(si.name)
			self._publish_all_outputs(si.name)

			out = StdInstanceReadinessService.evaluate(si.name)
			self.assertEqual(out["status"], "Ready")
			self.assertEqual(out["blockers"], [])

			inst = frappe.get_doc("Tender STD Instance", si.name)
			self.assertEqual(inst.readiness_status, "Ready")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0700_deterministic_blocker_order(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			out1 = StdInstanceReadinessService.evaluate(si.name, persist=False)
			out2 = StdInstanceReadinessService.evaluate(si.name, persist=False)
			self.assertEqual(out1["blockers"], out2["blockers"])
			self.assertEqual(out1["warnings"], out2["warnings"])
		finally:
			self._cleanup_tender(tender)
