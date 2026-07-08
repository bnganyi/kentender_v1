# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-0800 — addendum impact mapping and regeneration plan."""

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
from kentender_procurement.tender_management.std_instance.addendum import (
	StdAddendumImpactService,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)


class TestStdInstAddendumImpact0800(IntegrationTestCase):
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
		doc.tender_title = "STDINST-0800 Test Tender"
		doc.tender_reference = "STDINST0800-REF"
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

	def test_std_inst_0800_identify_affected_outputs_deterministic(self) -> None:
		out = StdAddendumImpactService.identify_affected_outputs(["submission_deadline", "contract_condition"])
		self.assertEqual(out, ["Bundle", "DSM", "DOM", "DCM"])

	def test_std_inst_0800_analyse_impact_supplier_notification(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			out = StdAddendumImpactService.analyse_impact(
				si.name,
				["evaluation_criteria", "contract_condition"],
				source_addendum_code="ADDM-1",
			)
			self.assertEqual(out["affected_outputs"], ["Bundle", "DEM", "DCM"])
			self.assertFalse(out["requires_supplier_notification"])
			self.assertTrue(out["requires_addendum_snapshot"])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0800_create_regeneration_plan_shape(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			plan = StdAddendumImpactService.create_regeneration_plan(
				si.name,
				["boq_quantity"],
				source_addendum_code="ADDM-2",
			)
			self.assertEqual(plan["affected_outputs"], ["Bundle", "DSM", "DEM", "DCM"])
			self.assertEqual(plan["snapshot_type"], "Addendum")
			self.assertEqual(len(plan["steps"]), 4)
			self.assertEqual(plan["steps"][0]["output_type"], "Bundle")
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_0800_execute_regeneration_creates_outputs_and_snapshot(self) -> None:
		tender = self._minimal_tender()
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender, ignore_permissions=True, record_template_usage=False
			)
			self._publish_all_outputs(si.name)
			res = StdAddendumImpactService.create_regeneration_plan(
				si.name,
				["submission_deadline"],
				source_addendum_code="ADDM-EXEC-1",
				execute=True,
				publish_outputs=True,
			)
			self.assertTrue(res["executed"])
			self.assertTrue(res["addendum_snapshot_code"])
			self.assertEqual(len(res["executed_outputs"]), 3)
			self.assertEqual(res["executed_outputs"][0]["output_type"], "Bundle")
		finally:
			self._cleanup_tender(tender)
