# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0320 — ``ReturnToPreparationService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_return_to_preparation_0320
"""

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
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.approval.return_to_preparation import (
	RETURN_TO_PREPARATION_PAYLOAD_INVALID,
	ReturnToPreparationService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubReturnToPreparation0320(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for dname in frappe.get_all(
			"Tender Publication Approval Decision",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender Publication Approval Decision",
				dname,
				force=True,
				ignore_permissions=True,
			)
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

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0320 {ref}"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		return doc.name

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

	def _locked_tender(self, ref: str) -> tuple[str, str]:
		tn = self._minimal_tender(ref=ref)
		frappe.db.set_value("TM2 Tender", tn, "source_package_code", f"REL-{ref}")
		si = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tn,
			ignore_permissions=True,
			record_template_usage=False,
		)
		StdInstanceParameterService.set_parameter_value(
			si.name,
			"submission_deadline",
			"2026-12-31",
			ignore_publication_lock=True,
		)
		StdInstanceWorksRequirementService.set_works_requirement(
			si.name,
			"WR-COMP-001",
			structured_text="PUB-0320 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		return tn, si.name

	def test_pub_0320_payload_requires_pack_fields(self) -> None:
		tn, _ = self._locked_tender("PUB0320-PAYLOAD")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ReturnToPreparationService.returnToPreparation(tn, {}, actor="Administrator")
			self.assertEqual(_last_msg_title(), RETURN_TO_PREPARATION_PAYLOAD_INVALID)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0320_invalid_criticality(self) -> None:
		tn, _ = self._locked_tender("PUB0320-CRIT")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ReturnToPreparationService.returnToPreparation(
					tn,
					{
						"return_reason_code": "X",
						"return_comment": "c",
						"affected_area": "BOQ",
						"criticality": "Severe",
					},
					actor="Administrator",
				)
			self.assertEqual(_last_msg_title(), RETURN_TO_PREPARATION_PAYLOAD_INVALID)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0320_happy_path_and_audits(self) -> None:
		tn, si_name = self._locked_tender("PUB0320-OK")
		try:
			before_ae = frappe.db.count("Audit Event", {"document_name": tn})
			out = ReturnToPreparationService.returnToPreparation(
				tn,
				{
					"return_reason_code": "BOQ_CORRECTION_REQUIRED",
					"return_comment": "BOQ item 2.2 requires correction before publication.",
					"affected_area": "BOQ",
					"criticality": "High",
				},
				actor="Administrator",
			)
			self.assertTrue(out.get("ok"))
			self.assertEqual(out.get("instance_status"), "In Configuration")
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"In Configuration",
			)
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
			self.assertEqual(PublicationReadinessService.getLatestReadiness(tn)["status"], "Invalidated")
			self.assertEqual((frappe.db.get_value("TM2 Tender", tn, "tender_status") or "").strip(), "Configured")

			after_ae = frappe.db.count("Audit Event", {"document_name": tn})
			self.assertGreaterEqual(after_ae, before_ae + 2)

			rtp = frappe.get_all(
				"Audit Event",
				filters={"document_name": tn, "event_type": "TENDER_PUBLICATION_RETURN_TO_PREPARATION"},
				limit=1,
			)
			self.assertTrue(rtp)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0320_target_validation_blocked(self) -> None:
		tn, si_name = self._locked_tender("PUB0320-VB")
		try:
			out = ReturnToPreparationService.returnToPreparation(
				tn,
				{
					"return_reason_code": "R1",
					"return_comment": "Need validation pass",
					"affected_area": "TDS",
					"criticality": "Medium",
					"target_instance_status": "Validation Blocked",
				},
				actor="Administrator",
			)
			self.assertEqual(out.get("instance_status"), "Validation Blocked")
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"Validation Blocked",
			)
		finally:
			self._cleanup_tender(tn)
