# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0610 — ``PublicationLockService`` and post-publication denial audit.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_publication_lock_0610
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
from kentender_procurement.tender_management.std_instance.drawing_register import (
	StdInstanceDrawingRegisterService,
)
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
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_POST_PUBLICATION_EDIT_DENIED,
	DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
)
from kentender_procurement.tender_management.tender_publication.publication.lock_service import (
	PublicationLockService,
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
from kentender_procurement.tender_management.tender_publication.snapshot.tender_publication_snapshot import (
	PublicationSnapshotService,
)


class TestPubPublicationLock0610(IntegrationTestCase):
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
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0610 {ref}"
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
			structured_text="PUB-0610 requirement.",
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

	def _denial_count(self, tender_name: str) -> int:
		return frappe.db.count(
			"Audit Event",
			{"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tender_name},
		)

	def _latest_denial_meta(self, tender_name: str) -> dict:
		rows = frappe.get_all(
			"Audit Event",
			filters={"event_type": AUDIT_POST_PUBLICATION_EDIT_DENIED, "document_name": tender_name},
			fields=["name", "metadata"],
			order_by="creation desc",
			limit=1,
		)
		self.assertTrue(rows, msg="expected a post-publication denial audit row")
		meta = rows[0].get("metadata") or {}
		if isinstance(meta, str):
			meta = json.loads(meta)
		return meta

	def test_pub_0610_tds_denied_with_audit(self) -> None:
		tn, si = self._approved_ready_tender("PUB0610-TDS")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			before = self._denial_count(tn)
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				StdInstanceParameterService.set_parameter_value(
					si,
					"submission_deadline",
					"2027-01-01",
				)
			self.assertEqual(self._denial_count(tn), before + 1)
			meta = self._latest_denial_meta(tn)
			self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)
			self.assertEqual(meta.get("attempted_change"), "edit parameters")
			self.assertEqual(meta.get("instance_code"), si)
			self.assertEqual(meta.get("tender_code"), tn)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0610_boq_denied_with_audit(self) -> None:
		tn, si = self._approved_ready_tender("PUB0610-BOQ")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			boq_name = frappe.db.get_value("Tender STD Instance BOQ", {"tender_std_instance": si}, "name")
			self.assertTrue(boq_name)
			before = self._denial_count(tn)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceBoqService.add_bill(
					boq_name,
					"9",
					"Late",
					"X",
					ignore_boq_publication_lock=False,
				)
			self.assertEqual(self._denial_count(tn), before + 1)
			meta = self._latest_denial_meta(tn)
			self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)
			self.assertEqual(meta.get("attempted_change"), "edit BOQ")
		finally:
			self._cleanup_tender(tn)

	def test_pub_0610_drawing_denied_with_audit(self) -> None:
		tn, si = self._approved_ready_tender("PUB0610-DRW")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			before = self._denial_count(tn)
			with self.assertRaises(frappe.ValidationError):
				StdInstanceDrawingRegisterService.set_drawing_row(
					si,
					drawing_code="DWG-PUB0610",
					revision="A",
					title="Plan",
					section_code="DRAWINGS",
				)
			self.assertEqual(self._denial_count(tn), before + 1)
			meta = self._latest_denial_meta(tn)
			self.assertEqual(meta.get("denial_code"), DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED)
			self.assertEqual(meta.get("attempted_change"), "edit drawing register")
		finally:
			self._cleanup_tender(tn)

	def test_pub_0610_assert_not_published_locked_by_tender_code(self) -> None:
		tn, si = self._approved_ready_tender("PUB0610-NTPL")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				PublicationLockService.assertNotPublishedLocked(tn)
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				PublicationLockService.assertNotPublishedLocked(si)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0610_assert_can_edit_pre_publication_denies_after_publish(self) -> None:
		tn, si = self._approved_ready_tender("PUB0610-PRE")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			with self.assertRaisesRegex(frappe.ValidationError, "addendum"):
				PublicationLockService.assertCanEditPrePublication(si, actor="Administrator")
		finally:
			self._cleanup_tender(tn)

	def test_pub_0610_mark_published_locked_rejects_foreign_snapshot(self) -> None:
		tn_a, si_a = self._approved_ready_tender("PUB0610-SN-A")
		tn_b, si_b = self._approved_ready_tender("PUB0610-SN-B")
		try:
			PublicationTransactionService.publishTender(tn_a, actor="Administrator")
			frappe.db.commit()
			snap = PublicationSnapshotService.getPublicationSnapshot(tn_a)
			self.assertIsNotNone(snap)
			snap_code = snap.get("snapshot_code")
			self.assertTrue(snap_code)
			with self.assertRaisesRegex(frappe.ValidationError, "does not belong"):
				PublicationLockService.markPublishedLocked(si_b, snap_code, actor="Administrator")
		finally:
			self._cleanup_tender(tn_a)
			self._cleanup_tender(tn_b)
