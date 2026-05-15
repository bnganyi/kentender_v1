# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-1200 — Publication smoke tests (Cursor pack §20 ``PUB-SMOKE-*``).

Each test method name includes its pack code. Assertions use stable denial titles /
finding codes from the publication readiness and precondition layers.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_smoke_1200
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	OutputConsumptionService,
)
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.drawing_register import (
	StdInstanceDrawingRegisterService,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
import kentender_procurement.tender_management.std_instance.publication_lock as std_pub_lock_mod
from kentender_procurement.tender_management.std_instance.parameter import StdInstanceParameterService
from kentender_procurement.tender_management.std_instance.readiness import StdInstanceReadinessService
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	ApprovalDecisionService,
	DECISION_APPROVED,
)
from kentender_procurement.tender_management.tender_publication.approval.return_to_preparation import (
	ReturnToPreparationService,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_POST_PUBLICATION_EDIT_DENIED,
	DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EXPORT_FORMAT_JSON_MANIFEST,
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.publication.precondition import (
	PUBLISH_APPROVAL_REQUIRED,
	PUBLISH_OUTPUT_STALE,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.seeds.seed_pub_moh_1100 import (
	fixture_codes,
	run as seed_pub_1100_run,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	CONFIG_SNAPSHOT_READINESS_REQUIRED,
	ConfigurationSnapshotService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.tender_publication_snapshot import (
	PublicationSnapshotService,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubSmoke1200(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()

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

	def _cleanup_seed_variant(self, variant: str) -> None:
		ref = fixture_codes(variant)["tender_reference"]
		tn = frappe.db.get_value("Procurement Tender", {"tender_reference": ref}, "name")
		if tn:
			self._cleanup_tender(tn)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-SMOKE {ref}"
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

	def _ready_tender_locked_for_approval(self, ref: str) -> tuple[str, str]:
		"""Ready STD + configuration snapshot + ``Locked for Approval`` (no approval row)."""
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
			structured_text="PUB-SMOKE requirement.",
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

	def _approved_publishable_fixture(self, ref: str) -> tuple[str, str]:
		tn, si = self._ready_tender_locked_for_approval(ref)
		ApprovalDecisionService.approveForPublication(tn, {"decision_note": "PUB-SMOKE"}, actor="Administrator")
		return tn, si

	# --- Readiness (PUB-SMOKE-READY-*) ---

	def test_PUB_SMOKE_READY_001_complete_tender_readiness_ready(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "ready")
		out = seed_pub_1100_run("ready")
		self.assertTrue(out.get("ok"))
		self.assertEqual(out.get("publication_readiness_status"), "Ready")

	def test_PUB_SMOKE_READY_002_missing_bundle_blocked(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "no_bundle")
		out = seed_pub_1100_run("no_bundle")
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		self.assertIn("BUNDLE_NOT_CURRENT", out.get("publication_finding_codes") or [])

	def test_PUB_SMOKE_READY_003_stale_dem_blocked(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "stale_dem")
		out = seed_pub_1100_run("stale_dem")
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		fc = set(out.get("publication_finding_codes") or [])
		self.assertTrue(
			"DEM_NOT_CURRENT" in fc or any("STALE" in c for c in fc),
			msg=f"expected DEM_NOT_CURRENT or stale-related code, got {fc}",
		)

	def test_PUB_SMOKE_READY_004_missing_std_binding_blocked(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "no_std_binding")
		out = seed_pub_1100_run("no_std_binding")
		self.assertEqual(out.get("publication_readiness_status"), "Blocked")
		self.assertIn("STD_BINDING_MISSING", out.get("publication_finding_codes") or [])

	def test_PUB_SMOKE_READY_005_missing_release_record_blocked(self) -> None:
		tn = self._minimal_tender(ref="PUB1200-RELMISS")
		try:
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
			res = PublicationReadinessService.runReadiness(tn, actor="Administrator")
			self.assertEqual(res.get("status"), "Blocked")
			self.assertIn("RELEASE_RECORD_MISSING", {f.get("code") for f in (res.get("findings") or [])})
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_READY_006_evidence_gate_failure_blocked(self) -> None:
		tn = self._minimal_tender(ref="PUB1200-EVID")
		try:
			frappe.db.set_value("Procurement Tender", tn, "source_package_code", "REL-PUB1200-EVID")
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
			with patch.object(
				EvidencePackageService,
				"validate_for_readiness_gate",
				return_value={"ok": False, "reason": "PUB-SMOKE-READY-006"},
			):
				res = PublicationReadinessService.runReadiness(tn, actor="Administrator")
			self.assertEqual(res.get("status"), "Blocked")
			self.assertIn("EVIDENCE_PACKAGE_FAILED", {f.get("code") for f in (res.get("findings") or [])})
		finally:
			self._cleanup_tender(tn)

	# --- Approval (PUB-SMOKE-APP-*) ---

	def test_PUB_SMOKE_APP_001_submit_ready_tender_configuration_snapshot(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "ready")
		out = seed_pub_1100_run("ready")
		tn = out["tender_name"]
		sub = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		self.assertTrue(sub.get("ok"))
		self.assertTrue((sub.get("snapshot") or "").strip())
		self.assertEqual((sub.get("instance_status") or "").strip(), "Locked for Approval")

	def test_PUB_SMOKE_APP_002_submit_blocked_tender_denied(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "no_bundle")
		out = seed_pub_1100_run("no_bundle")
		tn = out["tender_name"]
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		self.assertEqual(_last_msg_title(), CONFIG_SNAPSHOT_READINESS_REQUIRED)

	def test_PUB_SMOKE_APP_003_approver_boq_edit_denied(self) -> None:
		self.addCleanup(self._cleanup_seed_variant, "ready")
		out = seed_pub_1100_run("ready")
		tn = out["tender_name"]
		ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		si = out["std_instance_code"]
		self.assertTrue(si)
		boq_name = frappe.db.get_value("Tender STD Instance BOQ", {"tender_std_instance": si}, "name")
		self.assertTrue(boq_name)
		with self.assertRaises(frappe.ValidationError):
			StdInstanceBoqService.add_bill(
				boq_name,
				"9",
				"Approver edit",
				"Works",
				ignore_boq_publication_lock=False,
			)

	def test_PUB_SMOKE_APP_004_return_invalidates_snapshot(self) -> None:
		tn, si_name = self._ready_tender_locked_for_approval("PUB1200-RTP")
		try:
			out = ReturnToPreparationService.returnToPreparation(
				tn,
				{
					"return_reason_code": "BOQ_CORRECTION_REQUIRED",
					"return_comment": "PUB-SMOKE-APP-004 return",
					"affected_area": "BOQ",
					"criticality": "High",
				},
				actor="Administrator",
			)
			self.assertTrue(out.get("ok"))
			self.assertIsNone(ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tn))
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"In Configuration",
			)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_APP_005_approver_approves(self) -> None:
		tn, _si = self._ready_tender_locked_for_approval("PUB1200-APR")
		try:
			res = ApprovalDecisionService.approveForPublication(
				tn,
				{"decision_note": "PUB-SMOKE-APP-005"},
				actor="Administrator",
			)
			self.assertTrue(res.get("ok"))
			self.assertEqual(res.get("decision"), DECISION_APPROVED)
		finally:
			self._cleanup_tender(tn)

	# --- Publication (PUB-SMOKE-PUBLISH-*) ---

	def test_PUB_SMOKE_PUBLISH_001_publish_approved_tender(self) -> None:
		tn, si_name = self._approved_publishable_fixture("PUB1200-PUB1")
		try:
			res = PublicationTransactionService.publishTender(tn, actor="Administrator")
			self.assertTrue(res.get("ok"))
			self.assertEqual((res.get("tender_status") or "").strip(), "Published")
			snap = PublicationSnapshotService.getPublicationSnapshot(tn)
			self.assertIsNotNone(snap)
			self.assertEqual((snap.get("snapshot_status") or "").strip(), "Final")
			self.assertEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"Published Locked",
			)
			for field in (
				"current_bundle_output_code",
				"current_dsm_output_code",
				"current_dom_output_code",
				"current_dem_output_code",
				"current_dcm_output_code",
			):
				code = (frappe.db.get_value("Tender STD Instance", si_name, field) or "").strip()
				self.assertTrue(code)
				self.assertEqual(
					(frappe.db.get_value("Tender STD Generated Output", code, "output_status") or "").strip(),
					"Published",
				)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_PUBLISH_002_publish_without_approval_denied(self) -> None:
		tn, _si = self._ready_tender_locked_for_approval("PUB1200-NOAPR")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationTransactionService.publishTender(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_APPROVAL_REQUIRED)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_PUBLISH_003_snapshot_insert_failure_rollback(self) -> None:
		tn, _si = self._approved_publishable_fixture("PUB1200-SNAP3")
		try:
			before_final = frappe.db.count(
				"Tender Publication Snapshot",
				{"procurement_tender": tn, "snapshot_status": "Final"},
			)
			with patch.object(
				PublicationSnapshotService,
				"insert_publication_snapshots_after_precheck",
				side_effect=frappe.ValidationError("PUB-SMOKE-PUBLISH-003 fixture"),
			):
				with self.assertRaises(frappe.ValidationError):
					PublicationTransactionService.publishTender(tn, actor="Administrator")
			self.assertNotEqual(
				(frappe.db.get_value("Procurement Tender", tn, "tender_status") or "").strip(),
				"Published",
			)
			after_final = frappe.db.count(
				"Tender Publication Snapshot",
				{"procurement_tender": tn, "snapshot_status": "Final"},
			)
			self.assertEqual(after_final, before_final)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_PUBLISH_004_publish_stale_dsm_denied(self) -> None:
		tn, si_name = self._approved_publishable_fixture("PUB1200-STLE")
		try:
			StdInstanceGeneratedOutputService.mark_output_stale(si_name, output_type="DSM")
			pub_read_mod.clear_publication_readiness_cache()
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationTransactionService.publishTender(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), PUBLISH_OUTPUT_STALE)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_PUBLISH_005_partial_failure_rollback(self) -> None:
		tn, si_name = self._approved_publishable_fixture("PUB1200-RB")
		try:
			_real_apply = std_pub_lock_mod.StdInstanceStateService.apply_transition

			def _fail_on_published_lock(
				instance_name: str,
				to_status: str,
				*,
				ignore_permissions: bool = False,
			):
				if (to_status or "").strip() == "Published Locked":
					raise frappe.ValidationError("PUB-SMOKE-PUBLISH-005 fixture")
				return _real_apply(instance_name, to_status, ignore_permissions=ignore_permissions)

			with patch.object(
				std_pub_lock_mod.StdInstanceStateService,
				"apply_transition",
				staticmethod(_fail_on_published_lock),
			):
				with self.assertRaises(frappe.ValidationError):
					PublicationTransactionService.publishTender(tn, actor="Administrator")
			self.assertNotEqual(
				(frappe.db.get_value("Procurement Tender", tn, "tender_status") or "").strip(),
				"Published",
			)
			self.assertNotEqual(
				(frappe.db.get_value("Tender STD Instance", si_name, "instance_status") or "").strip(),
				"Published Locked",
			)
		finally:
			self._cleanup_tender(tn)

	# --- Post-publication (PUB-SMOKE-POST-*) ---

	def test_PUB_SMOKE_POST_001_edit_tds_denied(self) -> None:
		tn, si = self._approved_publishable_fixture("PUB1200-POST1")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				StdInstanceParameterService.set_parameter_value(
					si,
					"submission_deadline",
					"2027-06-01",
				)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_POST_002_edit_boq_denied(self) -> None:
		tn, si = self._approved_publishable_fixture("PUB1200-POST2")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			boq_name = frappe.db.get_value("Tender STD Instance BOQ", {"tender_std_instance": si}, "name")
			self.assertTrue(boq_name)
			before = frappe.db.count(
				"Audit Event",
				{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
			)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceBoqService.add_bill(
					boq_name,
					"99",
					"Late bill",
					"Works",
					ignore_boq_publication_lock=False,
				)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
				),
				before + 1,
			)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			self.assertTrue(rows)
			meta = rows[0].get("metadata") or {}
			if isinstance(meta, str):
				meta = json.loads(meta)
			self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_POST_003_replace_drawing_denied(self) -> None:
		tn, si = self._approved_publishable_fixture("PUB1200-POST3")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			with self.assertRaises(frappe.ValidationError):
				StdInstanceDrawingRegisterService.set_drawing_row(
					si,
					drawing_code="DWG-PUB1200",
					revision="A",
					title="Plan",
					section_code="DRAWINGS",
				)
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_POST_004_consume_published_dsm_submission_allowed(self) -> None:
		tn, si = self._approved_publishable_fixture("PUB1200-POST4")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			dsm = (frappe.db.get_value("Tender STD Instance", si, "current_dsm_output_code") or "").strip()
			self.assertTrue(dsm)
			env = OutputConsumptionService.validate_consumption(dsm, "Submission", None)
			self.assertTrue(env.get("allowed"), msg=str(env.get("blockers")))
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_POST_005_consume_published_dem_evaluation_allowed(self) -> None:
		tn, si = self._approved_publishable_fixture("PUB1200-POST5")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			dem = (frappe.db.get_value("Tender STD Instance", si, "current_dem_output_code") or "").strip()
			self.assertTrue(dem)
			env = OutputConsumptionService.validate_consumption(dem, "Evaluation", None)
			self.assertTrue(env.get("allowed"), msg=str(env.get("blockers")))
		finally:
			self._cleanup_tender(tn)

	def test_PUB_SMOKE_POST_006_export_evidence_allowed(self) -> None:
		tn, _si = self._approved_publishable_fixture("PUB1200-POST6")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			m = EvidencePackageService.exportEvidencePackage(
				tn,
				EXPORT_FORMAT_JSON_MANIFEST,
				actor="Administrator",
			)
			self.assertTrue(m.get("ok"))
			data = m.get("data") or {}
			self.assertEqual(data.get("tender_code"), tn)
		finally:
			self._cleanup_tender(tn)
