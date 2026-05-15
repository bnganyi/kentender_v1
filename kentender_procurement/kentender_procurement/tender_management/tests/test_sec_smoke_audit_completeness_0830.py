# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0830 — audit completeness smoke tests (`SEC-SMOKE-AUDIT-001` … `006`).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_smoke_audit_completeness_0830
"""

from __future__ import annotations

import json

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.events.codes import DERIVED_MODEL_GENERATED
from kentender_procurement.tender_management.derived_models.orchestration import DerivedModelGenerationService
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.security.audit.event_service import AuditEventService
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)
from kentender_procurement.tender_management.security.evidence.export_authorization import (
	EvidenceExportAuthorizationService,
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
from kentender_procurement.tender_management.tender_publication.approval.return_to_preparation import (
	ReturnToPreparationService,
)
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_POST_PUBLICATION_EDIT_DENIED,
	AUDIT_TENDER_PUBLICATION_ADDENDUM_REQUIRED_NOTICE,
	AUDIT_TENDER_PUBLICATION_PUBLICATION_SNAPSHOT_CREATED,
	AUDIT_TENDER_PUBLICATION_TENDER_PUBLISHED,
	DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)


class TestSecSmokeAuditCompleteness0830(IntegrationTestCase):
	@classmethod
	def setUpClass(cls) -> None:
		super().setUpClass()
		frappe.set_user("Administrator")
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	@classmethod
	def tearDownClass(cls) -> None:
		frappe.set_user("Administrator")
		super().tearDownClass()

	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		pub_read_mod.clear_publication_readiness_cache()
		super().tearDown()

	@staticmethod
	def _meta(value: object) -> dict:
		if isinstance(value, dict):
			return value
		if isinstance(value, str) and value.strip():
			try:
				out = json.loads(value)
			except Exception:
				return {}
			return out if isinstance(out, dict) else {}
		return {}

	def _delete_audits_for_doc(self, document_name: str) -> None:
		for name in frappe.get_all("Audit Event", filters={"document_name": document_name}, pluck="name"):
			frappe.delete_doc("Audit Event", name, force=True, ignore_permissions=True)

	def _cleanup_tender(self, tender_name: str) -> None:
		self._delete_audits_for_doc(tender_name)
		for dname in frappe.get_all(
			"Tender Publication Snapshot",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
			frappe.delete_doc("Tender Publication Snapshot", dname, force=True, ignore_permissions=True)
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
		doc.tender_title = f"SEC-0830 {ref}"
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
			structured_text="SEC-0830 requirement.",
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

	def _locked_for_return(self, ref: str) -> tuple[str, str]:
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
			structured_text="SEC-0830 RTP requirement.",
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

	def test_sec_smoke_audit_001_denied_action_creates_audit_event(self) -> None:
		"""SEC-SMOKE-AUDIT-001 — denied authorization persists denied audit with denial metadata."""
		fake = "SEC0830-AUDIT001-NONEXISTENT"
		self._delete_audits_for_doc(fake)
		try:
			with self.assertRaises(frappe.PermissionError):
				enforce_sec_authorization(
					action_code="PUBLISH_TENDER",
					actor="Administrator",
					object_type="Procurement Tender",
					object_code=fake,
					context={"object_exists": False},
					fallback_message="missing tender",
				)
			rows = AuditEventService.get_audit_events_for_object(
				"Procurement Tender",
				fake,
				{"result": "Denied"},
			)
			self.assertTrue(rows, msg="expected denied-action audit row")
			meta = self._meta(rows[0].get("metadata"))
			self.assertEqual(meta.get("result"), "Denied")
			self.assertEqual(meta.get("action_code"), "PUBLISH_TENDER")
			self.assertEqual(meta.get("denial_code"), DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED)
		finally:
			self._delete_audits_for_doc(fake)

	def test_sec_smoke_audit_002_publication_creates_snapshot_and_tender_published_audits(self) -> None:
		"""SEC-SMOKE-AUDIT-002 — successful publish emits publication snapshot + tender published audits."""
		tn, _si = self._approved_ready_tender("SEC0830-AUDIT002")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			snap_rows = AuditEventService.get_audit_events_for_tender(
				tn,
				{"event_type": AUDIT_TENDER_PUBLICATION_PUBLICATION_SNAPSHOT_CREATED},
			)
			self.assertTrue(snap_rows, msg="expected publication snapshot audit")
			pub_rows = AuditEventService.get_audit_events_for_tender(
				tn,
				{"event_type": AUDIT_TENDER_PUBLICATION_TENDER_PUBLISHED},
			)
			self.assertTrue(pub_rows, msg="expected tender published audit")
			smeta = self._meta(snap_rows[0].get("metadata"))
			self.assertEqual(smeta.get("tender_code"), tn)
			pmeta = self._meta(pub_rows[0].get("metadata"))
			self.assertEqual(pmeta.get("tender_code"), tn)
		finally:
			self._cleanup_tender(tn)

	def test_sec_smoke_audit_003_evidence_export_audited_with_hash(self) -> None:
		"""SEC-SMOKE-AUDIT-003 — authorized evidence export records success audit with package hash."""
		tn = self._minimal_tender(ref="SEC0830-AUDIT003")
		try:
			h = "sha256:sec0830_evidence_test_hash"
			name = EvidenceExportAuthorizationService.record_evidence_export(
				"Administrator",
				tn,
				"JSON_MANIFEST",
				h,
			)
			self.assertTrue(name)
			meta = self._meta(frappe.db.get_value("Audit Event", name, "metadata"))
			self.assertEqual(meta.get("evidence_package_hash"), h)
			self.assertEqual(meta.get("action_code"), "EXPORT_EVIDENCE_PACKAGE")
			self.assertEqual((meta.get("result") or "").lower(), "success")
		finally:
			self._cleanup_tender(tn)

	def test_sec_smoke_audit_004_output_generation_audited(self) -> None:
		"""SEC-SMOKE-AUDIT-004 — derived output generation emits DERIVED_MODEL_GENERATED audit."""
		tn = self._minimal_tender(ref="SEC0830-AUDIT004")
		frappe.db.set_value("Procurement Tender", tn, "source_package_code", "REL-SEC0830-A4")
		si = TenderStdBindingService.create_std_instance_for_tm2_tender(
			tn,
			ignore_permissions=True,
			record_template_usage=False,
		)
		try:
			before = frappe.db.count("Audit Event", {"event_type": DERIVED_MODEL_GENERATED})
			DerivedModelGenerationService.generate_output(si.name, "DSM", actor_or_job="Administrator")
			after = frappe.db.count("Audit Event", {"event_type": DERIVED_MODEL_GENERATED})
			self.assertGreater(after, before)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": DERIVED_MODEL_GENERATED},
				fields=["metadata", "document_name"],
				order_by="creation desc",
				limit=3,
			)
			self.assertTrue(rows)
			found = False
			for row in rows:
				meta = self._meta(row.get("metadata"))
				if meta.get("instance_code") == si.name and meta.get("output_type") == "DSM":
					found = True
					break
			self.assertTrue(found, msg="expected DSM generation audit for instance")
		finally:
			self._cleanup_tender(tn)

	def test_sec_smoke_audit_005_return_to_preparation_audited(self) -> None:
		"""SEC-SMOKE-AUDIT-005 — return-to-preparation orchestration emits dedicated audit event."""
		tn, _si = self._locked_for_return("SEC0830-AUDIT005")
		try:
			before = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": "TENDER_PUBLICATION_RETURN_TO_PREPARATION"},
			)
			out = ReturnToPreparationService.returnToPreparation(
				tn,
				{
					"return_reason_code": "BOQ_CORRECTION_REQUIRED",
					"return_comment": "SEC-0830 smoke return path.",
					"affected_area": "BOQ",
					"criticality": "High",
				},
				actor="Administrator",
			)
			self.assertTrue(out.get("ok"))
			after = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": "TENDER_PUBLICATION_RETURN_TO_PREPARATION"},
			)
			self.assertGreater(after, before)
		finally:
			self._cleanup_tender(tn)

	def test_sec_smoke_audit_006_addendum_required_denial_audited(self) -> None:
		"""SEC-SMOKE-AUDIT-006 — post-publication edit denial + addendum notice audits."""
		tn, si = self._approved_ready_tender("SEC0830-AUDIT006")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			before_denied = frappe.db.count(
				"Audit Event",
				{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
			)
			before_notice = frappe.db.count(
				"Audit Event",
				{"event_type": AUDIT_TENDER_PUBLICATION_ADDENDUM_REQUIRED_NOTICE, "document_name": tn},
			)
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				StdInstanceParameterService.set_parameter_value(
					si,
					"submission_deadline",
					"2027-06-01",
				)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
				),
				before_denied + 1,
			)
			self.assertEqual(
				frappe.db.count(
					"Audit Event",
					{"event_type": AUDIT_TENDER_PUBLICATION_ADDENDUM_REQUIRED_NOTICE, "document_name": tn},
				),
				before_notice + 1,
			)
			rows = frappe.get_all(
				"Audit Event",
				filters={"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tn},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			self.assertTrue(rows)
			meta = self._meta(rows[0].get("metadata"))
			self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)
		finally:
			self._cleanup_tender(tn)
