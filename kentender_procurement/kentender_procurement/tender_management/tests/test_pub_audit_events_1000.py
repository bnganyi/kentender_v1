# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-1000 — publication ``Audit Event`` catalogue (pack §18).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_audit_events_1000
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
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_PUBLICATION_DENIED,
	AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED,
	AUDIT_TENDER_PUBLICATION_TENDER_PUBLISHED,
	PACK_PUBLICATION_DENIED,
	PACK_PUBLICATION_READINESS_BLOCKED,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.tender_publication.publication.transaction import (
	PublicationTransactionService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.approval.approval_decision import (
	ApprovalDecisionService,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
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


class TestPubAuditEvents1000(IntegrationTestCase):
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
		doc.tender_title = f"PUB-1000 {ref}"
		doc.tender_reference = ref
		doc.insert(ignore_permissions=True)
		return doc.name

	def test_pub_1000_readiness_blocked_emits_audit(self) -> None:
		ref = f"PUB1000-BLK-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			before = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED},
			)
			PublicationReadinessService.runReadiness(tn, actor="Administrator")
			after = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED},
			)
			self.assertGreater(after, before)
			row = frappe.get_all(
				"Audit Event",
				filters={"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_READINESS_BLOCKED},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			meta = frappe.parse_json(row[0].get("metadata") or "{}")
			self.assertEqual(meta.get("event_code"), PACK_PUBLICATION_READINESS_BLOCKED)
		finally:
			self._cleanup_tender(tn)

	def test_pub_1000_emit_helper_pack_event_code(self) -> None:
		ref = f"PUB1000-EM-{frappe.generate_hash(length=6)}"
		tn = self._minimal_tender(ref=ref)
		try:
			name = emit_publication_audit_event(
				event_type=AUDIT_TENDER_PUBLICATION_TENDER_PUBLISHED,
				tender_code=tn,
				action="test_fixture",
				performed_by="Administrator",
				instance_code="STDINST-TEST",
				publication_snapshot_code="SNAP-TEST",
				details={"probe": True},
			)
			self.assertTrue(frappe.db.exists("Audit Event", name))
			meta = frappe.parse_json(frappe.db.get_value("Audit Event", name, "metadata") or "{}")
			self.assertEqual(meta.get("event_code"), "TENDER_PUBLISHED")
			self.assertEqual(meta.get("tender_code"), tn)
			self.assertEqual(meta.get("instance_code"), "STDINST-TEST")
			self.assertEqual(meta.get("publication_snapshot_code"), "SNAP-TEST")
		finally:
			self._cleanup_tender(tn)

	def test_pub_1000_second_publish_emits_denied(self) -> None:
		ref = f"PUB1000-DNY-{frappe.generate_hash(length=6)}"
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
			structured_text="PUB-1000 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		boq = StdInstanceBoqService.create_boq_for_instance(si.name, ignore_boq_publication_lock=True)
		boq = StdInstanceBoqService.add_bill(boq.name, "1", "General", "Works", ignore_boq_publication_lock=True)
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
		for fn in (
			StdInstanceGeneratedOutputService.generate_bundle,
			StdInstanceGeneratedOutputService.generate_dsm,
			StdInstanceGeneratedOutputService.generate_dom,
			StdInstanceGeneratedOutputService.generate_dem,
			StdInstanceGeneratedOutputService.generate_dcm,
		):
			out = fn(si.name)
			StdInstanceGeneratedOutputService.publish_output(out.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		try:
			ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
			ApprovalDecisionService.approveForPublication(tn, {"decision_note": "ok"}, actor="Administrator")
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			before = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_PUBLICATION_DENIED},
			)
			with self.assertRaises(frappe.ValidationError):
				PublicationTransactionService.publishTender(tn, actor="Administrator")
			after = frappe.db.count(
				"Audit Event",
				{"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_PUBLICATION_DENIED},
			)
			self.assertGreater(after, before)
			row = frappe.get_all(
				"Audit Event",
				filters={"document_name": tn, "event_type": AUDIT_TENDER_PUBLICATION_PUBLICATION_DENIED},
				fields=["metadata"],
				order_by="creation desc",
				limit=1,
			)
			meta = frappe.parse_json(row[0].get("metadata") or "{}")
			self.assertEqual(meta.get("event_code"), PACK_PUBLICATION_DENIED)
		finally:
			self._cleanup_tender(tn)
