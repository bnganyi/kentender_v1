# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0310 — ``ApprovalDecisionService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_approval_decision_0310
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
	APPROVAL_DECISION_ALREADY_APPROVED,
	APPROVAL_DECISION_PAYLOAD_INVALID,
	APPROVAL_DECISION_PRECONDITION_FAILED,
	APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT,
	APPROVAL_DECISION_STATE_CONFLICT,
	ApprovalDecisionService,
	DECISION_APPROVED,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_review_package import (
	ApprovalReviewPackageService,
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


class TestPubApprovalDecision0310(IntegrationTestCase):
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
		if frappe.db.exists("Procurement Tender", tender_name):
			frappe.delete_doc("Procurement Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0310 {ref}"
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

	def _locked_tender_with_snapshot(self, ref: str) -> tuple[str, str, str]:
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
			structured_text="PUB-0310 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		out = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		return tn, si.name, out["snapshot"]

	def test_pub_0310_precondition_without_snapshot(self) -> None:
		tn = self._minimal_tender(ref="PUB0310-NOSNAP")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalDecisionService.approveForPublication(tn, {}, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_DECISION_PRECONDITION_FAILED)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_approve_and_duplicate_denied(self) -> None:
		tn, si_name, snap_name = self._locked_tender_with_snapshot("PUB0310-APPR")
		try:
			r1 = ApprovalDecisionService.approveForPublication(tn, {"decision_note": "ok"}, actor="Administrator")
			self.assertTrue(r1.get("ok"))
			self.assertEqual(r1.get("decision"), DECISION_APPROVED)
			row = frappe.get_doc("Tender Publication Approval Decision", r1["decision_code"])
			self.assertEqual(row.configuration_snapshot, snap_name)
			self.assertEqual((row.decision or "").strip(), DECISION_APPROVED)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"Locked for Approval",
			)

			events = frappe.get_all(
				"Audit Event",
				filters={"document_name": tn, "event_type": "TENDER_PUBLICATION_APPROVAL_GRANTED"},
				pluck="name",
				limit=1,
			)
			self.assertTrue(events)

			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalDecisionService.approveForPublication(tn, {}, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_DECISION_ALREADY_APPROVED)

			pkg = ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor="Administrator")
			actions = (pkg["sections"].get("14_available_approval_actions") or {}).get("actions") or []
			self.assertFalse(next(a for a in actions if a["code"] == "APPROVE_FOR_PUBLICATION")["available"])
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_return_unlocks_and_invalidates_readiness(self) -> None:
		tn, si_name, _snap_name = self._locked_tender_with_snapshot("PUB0310-RET")
		try:
			ApprovalDecisionService.returnForCorrection(
				tn,
				{"return_comment": "Fix BOQ line 2"},
				actor="Administrator",
			)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"In Configuration",
			)
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
			self.assertEqual(PublicationReadinessService.getLatestReadiness(tn)["status"], "Invalidated")
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_reject_requires_note(self) -> None:
		tn, _, _ = self._locked_tender_with_snapshot("PUB0310-REJ")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalDecisionService.rejectPublication(tn, {}, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_DECISION_PAYLOAD_INVALID)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_clarification_keeps_lock(self) -> None:
		tn, si_name, _ = self._locked_tender_with_snapshot("PUB0310-CLR")
		try:
			ApprovalDecisionService.requestClarification(
				tn,
				{"clarification_summary": "Please confirm opening date"},
				actor="Administrator",
			)
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"Locked for Approval",
			)
			self.assertIsNotNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_denies_when_snapshot_readiness_has_critical(self) -> None:
		tn, _, snap_name = self._locked_tender_with_snapshot("PUB0310-BLOCK")
		try:
			tampered = {
				"status": "Ready",
				"findings": [
					{
						"code": "TDS_INCOMPLETE",
						"severity": "Critical",
						"message": "Tampered",
						"affected_area": "STD Completion",
						"resolution_action": "Fix",
						"blocks_approval": True,
						"blocks_publication": True,
					}
				],
			}
			frappe.db.set_value(
				"Tender STD Instance Snapshot",
				snap_name,
				"readiness_summary_json",
				json.dumps(tampered),
				update_modified=False,
			)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalDecisionService.approveForPublication(tn, {}, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_DECISION_READINESS_BLOCKERS_PRESENT)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0310_no_return_after_approve(self) -> None:
		tn, _, _ = self._locked_tender_with_snapshot("PUB0310-AFTER")
		try:
			ApprovalDecisionService.approveForPublication(tn, {}, actor="Administrator")
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalDecisionService.returnForCorrection(
					tn,
					{"return_comment": "too late"},
					actor="Administrator",
				)
			self.assertEqual(_last_msg_title(), APPROVAL_DECISION_STATE_CONFLICT)
		finally:
			self._cleanup_tender(tn)
