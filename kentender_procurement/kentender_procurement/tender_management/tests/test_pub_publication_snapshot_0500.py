# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0500 — ``PublicationSnapshotService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_publication_snapshot_0500
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
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	ApprovalDecisionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.tender_publication.publication.precondition import (
	PUBLISH_OUTPUT_STALE,
)
from kentender_procurement.tender_management.tender_publication.snapshot.tender_publication_snapshot import (
	PUBLICATION_SNAPSHOT_ALREADY_FINAL,
	PublicationSnapshotService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubPublicationSnapshot0500(IntegrationTestCase):
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
			"Tender Publication Snapshot",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc(
				"Tender Publication Snapshot",
				dname,
				force=True,
				ignore_permissions=True,
			)
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0500 {ref}"
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

	def _approved_ready_tender(self, ref: str) -> tuple[str, str]:
		tn = self._minimal_tender(ref=ref)
		frappe.db.set_value("Procurement Tender", tn, "source_package_code", f"REL-{ref}")
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
			structured_text="PUB-0500 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		ApprovalDecisionService.approveForPublication(tn, {"decision_note": "ok"}, actor="Administrator")
		return tn, si.name

	def test_pub_0500_create_and_get(self) -> None:
		tn, _si = self._approved_ready_tender("PUB0500-CR")
		try:
			out = PublicationSnapshotService.createPublicationSnapshot(tn, actor="Administrator")
			self.assertTrue(out.get("ok"))
			snap = out["publication_snapshot"]
			self.assertEqual(snap["tender_code"], tn)
			for k in (
				"bundle_output_code",
				"dsm_output_code",
				"dom_output_code",
				"dem_output_code",
				"dcm_output_code",
			):
				self.assertTrue((snap.get(k) or "").strip(), msg=k)
			self.assertTrue((snap.get("readiness_result_code") or "").startswith("READINESS|"))
			self.assertTrue((snap.get("evidence_package_code") or "").startswith("EVIDENCE|"))
			self.assertEqual(len((snap.get("complete_publication_hash") or "").strip()), 64)
			self.assertEqual(snap.get("snapshot_status"), "Final")

			got = PublicationSnapshotService.getPublicationSnapshot(tn)
			self.assertIsNotNone(got)
			self.assertEqual(got["snapshot_code"], snap["snapshot_code"])
			self.assertEqual(got["complete_publication_hash"], snap["complete_publication_hash"])
		finally:
			self._cleanup_tender(tn)

	def test_pub_0500_second_create_denied(self) -> None:
		tn, _si = self._approved_ready_tender("PUB0500-DUP")
		try:
			PublicationSnapshotService.createPublicationSnapshot(tn, actor="Administrator")
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationSnapshotService.createPublicationSnapshot(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLICATION_SNAPSHOT_ALREADY_FINAL)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0500_final_row_immutable(self) -> None:
		tn, _si_name = self._approved_ready_tender("PUB0500-IMM")
		try:
			res = PublicationSnapshotService.createPublicationSnapshot(tn, actor="Administrator")
			name = res["publication_snapshot"]["snapshot_code"]
			doc = frappe.get_doc("Tender Publication Snapshot", name)
			doc.bundle_output_code = "INVALID-OVERRIDE"
			with self.assertRaises(frappe.ValidationError):
				doc.save(ignore_permissions=True)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0500_stale_output_after_approve_denied(self) -> None:
		tn, si_name = self._approved_ready_tender("PUB0500-STALE")
		try:
			StdInstanceGeneratedOutputService.mark_output_stale(si_name, output_type="DEM")
			pub_read_mod.clear_publication_readiness_cache()
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationSnapshotService.createPublicationSnapshot(tn, actor="Administrator")
			# Precondition runs first; title is pack PUBLISH_* not snapshot-specific.
			self.assertEqual(_last_msg_title(), PUBLISH_OUTPUT_STALE)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0500_get_none_when_missing(self) -> None:
		tn = self._minimal_tender(ref="PUB0500-NONE")
		try:
			self.assertIsNone(PublicationSnapshotService.getPublicationSnapshot(tn))
		finally:
			self._cleanup_tender(tn)
