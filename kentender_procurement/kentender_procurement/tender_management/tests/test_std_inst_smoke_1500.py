# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STDINST-1500 — smoke contracts across creation/readiness/publication/addendum/downstream."""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_governance import STATUS_IMPORTED
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.addendum import (
	StdAddendumImpactService,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.downstream import (
	StdDownstreamConsumptionService,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.publication_lock import (
	StdPublicationLockService,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.snapshot import (
	StdInstanceSnapshotService,
)
from kentender_procurement.tender_management.std_instance.state import (
	StdInstanceStateService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)


class TestStdInstSmoke1500(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _minimal_tender(self, suffix: str) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"STDINST-1500 Smoke Tender {suffix}"
		doc.tender_reference = f"STDINST1500-{suffix}"
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

	def _configure_minimum_inputs(self, instance_name: str) -> None:
		StdInstanceParameterService.set_parameter_value(instance_name, "submission_deadline", "2026-12-31")
		StdInstanceWorksRequirementService.set_works_requirement(
			instance_name,
			"SPEC-SMOKE",
			requirement_status="Complete",
			structured_text="Smoke baseline specification",
			attachment_required=False,
			attachment_status="Not Required",
		)

	def _ensure_minimum_boq(self, instance_name: str) -> str:
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
		return boq.name

	def _publish_all_outputs(self, instance_name: str) -> dict[str, str]:
		created: dict[str, str] = {}
		for output_type, fn in (
			("Bundle", StdInstanceGeneratedOutputService.generate_bundle),
			("DSM", StdInstanceGeneratedOutputService.generate_dsm),
			("DOM", StdInstanceGeneratedOutputService.generate_dom),
			("DEM", StdInstanceGeneratedOutputService.generate_dem),
			("DCM", StdInstanceGeneratedOutputService.generate_dcm),
		):
			doc = fn(instance_name)
			doc = StdInstanceGeneratedOutputService.publish_output(doc.name)
			created[output_type] = doc.name
		return created

	def _create_publishable_instance(self, suffix: str) -> tuple[str, str]:
		tender = self._minimal_tender(suffix)
		si = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tender,
			ignore_permissions=True,
			record_template_usage=False,
		)
		self._configure_minimum_inputs(si.name)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		return tender, si.name

	def test_std_inst_1500_creation_smoke_contracts(self) -> None:
		tender = self._minimal_tender("CRT")
		try:
			created = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self.assertTrue(created.name)

			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					"NONEXISTENT-TENDER-STDINST1500",
					ignore_permissions=True,
					record_template_usage=False,
				)

			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					tender,
					ignore_permissions=True,
					record_template_usage=False,
				)

			frappe.db.set_value("STD Template", TEMPLATE_CODE, "lifecycle_status", STATUS_IMPORTED)
			inactive_tender = self._minimal_tender("CRT-INACTIVE")
			with self.assertRaises(frappe.ValidationError):
				TenderStdBindingService.create_std_instance_for_tm2_tender(
					inactive_tender,
					ignore_permissions=True,
					record_template_usage=False,
				)
			self._cleanup_tender(inactive_tender)
		finally:
			seed_std_template_governance_for_existing_works_poc(force_mode="active")
			self._cleanup_tender(tender)

	def test_std_inst_1500_readiness_smoke_contracts(self) -> None:
		tender = self._minimal_tender("READ")
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				tender,
				ignore_permissions=True,
				record_template_usage=False,
			)
			self._configure_minimum_inputs(si.name)
			self._publish_all_outputs(si.name)

			missing_boq = StdInstanceReadinessService.evaluate(si.name)
			missing_boq_codes = [row["code"] for row in missing_boq["blockers"]]
			self.assertEqual(missing_boq["status"], "Blocked")
			self.assertIn("BOQ_MISSING", missing_boq_codes)

			self._ensure_minimum_boq(si.name)
			self._publish_all_outputs(si.name)
			StdInstanceGeneratedOutputService.mark_output_stale(si.name, output_type="DEM")
			stale_dem = StdInstanceReadinessService.evaluate(si.name)
			stale_dem_codes = [row["code"] for row in stale_dem["blockers"]]
			self.assertEqual(stale_dem["status"], "Blocked")
			self.assertIn("DEM_MISSING", stale_dem_codes)
			self.assertIn("STALE_OUTPUTS_PRESENT", stale_dem_codes)

			StdInstanceGeneratedOutputService.publish_output(StdInstanceGeneratedOutputService.generate_dem(si.name).name)
			ready = StdInstanceReadinessService.evaluate(si.name)
			self.assertEqual(ready["status"], "Ready")
			self.assertEqual(ready["blockers"], [])
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1500_publication_smoke_contracts(self) -> None:
		tender, instance_name = self._create_publishable_instance("PUB")
		try:
			with self.assertRaises(frappe.ValidationError):
				StdPublicationLockService.lock_for_publication(instance_name)

			StdInstanceSnapshotService.create_publication_snapshot(
				instance_name,
				"STDINST-1500 publication smoke",
			)
			StdInstanceStateService.apply_transition(instance_name, "In Configuration", ignore_permissions=True)
			StdInstanceStateService.apply_transition(instance_name, "Ready for Publication", ignore_permissions=True)
			StdPublicationLockService.lock_for_approval(instance_name)
			StdPublicationLockService.lock_for_publication(instance_name)

			with self.assertRaises(frappe.ValidationError):
				StdInstanceParameterService.set_parameter_value(instance_name, "submission_deadline", "2027-01-01")

			bundle_code = frappe.db.get_value("Tender STD Instance", instance_name, "current_bundle_output_code")
			doc = frappe.get_doc("Tender STD Generated Output", bundle_code)
			payload = json.loads(doc.content_json) if isinstance(doc.content_json, str) else dict(doc.content_json or {})
			payload["tampered"] = True
			doc.content_json = payload
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1500_addendum_smoke_contracts(self) -> None:
		tender, instance_name = self._create_publishable_instance("ADD")
		try:
			old_outputs = {
				row.output_type: row.name
				for row in frappe.get_all(
					"Tender STD Generated Output",
					filters={"tender_std_instance": instance_name, "output_status": "Published"},
					fields=["name", "output_type"],
				)
			}
			result = StdAddendumImpactService.create_regeneration_plan(
				instance_name,
				["submission_deadline"],
				source_addendum_code="ADDM-1500-1",
				execute=True,
				publish_outputs=True,
			)
			self.assertTrue(result.get("executed"))
			self.assertTrue(result.get("addendum_snapshot_code"))

			new_outputs = {row["output_type"]: row["output_code"] for row in result["executed_outputs"]}
			self.assertIn("Bundle", new_outputs)
			self.assertNotEqual(new_outputs["Bundle"], old_outputs["Bundle"])
			self.assertTrue(frappe.db.exists("Tender STD Generated Output", old_outputs["Bundle"]))
			self.assertTrue(frappe.db.exists("Tender STD Generated Output", new_outputs["Bundle"]))
		finally:
			self._cleanup_tender(tender)

	def test_std_inst_1500_downstream_smoke_contracts(self) -> None:
		tender, instance_name = self._create_publishable_instance("DWN")
		try:
			self.assertTrue(StdDownstreamConsumptionService.get_current_dsm(instance_name)["output_code"])
			self.assertTrue(StdDownstreamConsumptionService.get_current_dom(instance_name)["output_code"])
			self.assertTrue(StdDownstreamConsumptionService.get_current_dem(instance_name)["output_code"])
			self.assertTrue(StdDownstreamConsumptionService.get_current_dcm(instance_name)["output_code"])

			with self.assertRaisesRegex(frappe.ValidationError, "must originate from STD outputs"):
				StdDownstreamConsumptionService.deny_manual_rule_injection(context="submission")
		finally:
			self._cleanup_tender(tender)
