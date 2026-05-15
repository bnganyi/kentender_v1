# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0400 — ``PublicationPreconditionService.assertCanPublish``.

Run (9 tests)::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_precondition_0400
"""

from __future__ import annotations

from unittest.mock import patch

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
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.publication.precondition import (
	PUBLISH_APPROVAL_REQUIRED,
	PUBLISH_CONFIGURATION_SNAPSHOT_MISSING,
	PUBLISH_EVIDENCE_PACKAGE_FAILED,
	PUBLISH_OUTPUT_MISSING,
	PUBLISH_OUTPUT_STALE,
	PUBLISH_PERMISSION_DENIED,
	PUBLISH_READINESS_NOT_READY,
	PublicationPreconditionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubPrecondition0400(IntegrationTestCase):
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

	def _cleanup_user(self, email: str) -> None:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0400 {ref}"
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

	def _approved_locked_fixture(self, ref: str) -> tuple[str, str]:
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
			structured_text="PUB-0400 requirement.",
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

	def test_pub_0400_happy_path(self) -> None:
		tn, _si = self._approved_locked_fixture("PUB0400-OK")
		try:
			PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_missing_configuration_snapshot(self) -> None:
		tn = self._minimal_tender(ref="PUB0400-NOCFG")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_CONFIGURATION_SNAPSHOT_MISSING)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_without_approval(self) -> None:
		tn = self._minimal_tender(ref="PUB0400-NOAPR")
		try:
			frappe.db.set_value("TM2 Tender", tn, "source_package_code", "REL-PUB0400-NOAPR")
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
				structured_text="x",
				requirement_status="Complete",
				attachment_required=False,
				attachment_status="Not Required",
				ignore_publication_lock=True,
			)
			self._ensure_minimum_boq(si.name)
			self._publish_all_outputs(si.name)
			ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_APPROVAL_REQUIRED)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_permission_denied(self) -> None:
		email = "pub0400_noperm@example.com"
		self._cleanup_user(email)
		tn, _si_name = self._approved_locked_fixture("PUB0400-PERM")
		try:
			u = frappe.new_doc("User")
			u.email = email
			u.first_name = "PUB0400"
			u.send_welcome_email = 0
			u.insert(ignore_permissions=True)
			# Role must exist on site; must not include System Manager / Purchase Manager.
			u.add_roles("Desk User")
			frappe.set_user(email)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor=email)
			self.assertEqual(_last_msg_title(), PUBLISH_PERMISSION_DENIED)
		finally:
			frappe.set_user("Administrator")
			self._cleanup_user(email)
			self._cleanup_tender(tn)

	def test_pub_0400_stale_output_denied(self) -> None:
		tn, si_name = self._approved_locked_fixture("PUB0400-STALE")
		try:
			StdInstanceGeneratedOutputService.mark_output_stale(si_name, output_type="DSM")
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_OUTPUT_STALE)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_output_missing_denied(self) -> None:
		tn, si_name = self._approved_locked_fixture("PUB0400-MISS")
		try:
			frappe.db.set_value(
				"Tender STD Instance",
				si_name,
				{
					"current_bundle_output_code": None,
					"outputs_stale_flags": "[]",
				},
			)
			pub_read_mod.clear_publication_readiness_cache()
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_OUTPUT_MISSING)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_evidence_package_failed(self) -> None:
		tn, _si = self._approved_locked_fixture("PUB0400-EVID")
		try:
			with patch.object(
				EvidencePackageService,
				"validateEvidencePackage",
				return_value={"ok": False, "reason": "fixture", "message": "fixture"},
			):
				frappe.clear_messages()
				with self.assertRaises(frappe.ValidationError):
					PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_EVIDENCE_PACKAGE_FAILED)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_readiness_not_ready_generic(self) -> None:
		tn, _si_name = self._approved_locked_fixture("PUB0400-RNR")
		try:
			frappe.db.set_value("TM2 Tender", tn, "source_package_code", "")
			pub_read_mod.clear_publication_readiness_cache()
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_READINESS_NOT_READY)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0400_instance_not_locked_for_approval(self) -> None:
		tn, si_name = self._approved_locked_fixture("PUB0400-UNLOCK")
		try:
			frappe.db.set_value("Tender STD Instance", si_name, "instance_status", "Ready for Publication")
			pub_read_mod.clear_publication_readiness_cache()
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationPreconditionService.assertCanPublish(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_APPROVAL_REQUIRED)
		finally:
			self._cleanup_tender(tn)
