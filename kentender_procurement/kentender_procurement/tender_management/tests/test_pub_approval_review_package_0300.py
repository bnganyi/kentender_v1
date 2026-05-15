# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0300 — ``ApprovalReviewPackageService`` (read-only review package from configuration snapshot).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_approval_review_package_0300
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
from kentender_procurement.tender_management.tender_publication.approval.approval_review_package import (
	APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED,
	ApprovalReviewPackageService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubApprovalReviewPackage0300(IntegrationTestCase):
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
		doc.tender_title = f"PUB-0300 {ref}"
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

	def _ready_tender_with_snapshot(self, ref: str) -> tuple[str, str, str]:
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
			structured_text="PUB-0300 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		lock_out = ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		snap_name = lock_out["snapshot"]
		return tn, si.name, snap_name

	def test_pub_0300_requires_configuration_snapshot(self) -> None:
		tn = self._minimal_tender(ref="PUB0300-NOSNAP")
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0300_package_bound_to_snapshot(self) -> None:
		tn, si_name, snap_name = self._ready_tender_with_snapshot("PUB0300-PKG")
		try:
			snap = frappe.get_doc("Tender STD Instance Snapshot", snap_name)
			self.assertTrue(_strip(getattr(snap, "readiness_summary_json", "") or ""))

			pkg = ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor="Administrator")
			self.assertTrue(pkg.get("read_only"))
			self.assertEqual(pkg.get("configuration_snapshot_code"), snap_name)
			sec = pkg.get("sections") or {}
			for key in (
				"1_tender_summary",
				"2_procurement_package",
				"3_std_template_profile",
				"4_readiness_result",
				"5_bundle",
				"6_dsm",
				"7_dom",
				"8_dem",
				"9_dcm",
				"10_boq",
				"11_works_spec_drawings",
				"12_blockers_and_warnings",
				"13_audit_evidence_summary",
				"14_available_approval_actions",
			):
				self.assertIn(key, sec, msg=f"missing {key}")

			self.assertEqual((sec["4_readiness_result"] or {}).get("status"), "Ready")
			self.assertEqual(
				(sec["5_bundle"] or {}).get("reference"),
				(snap.ref_bundle_output or "").strip(),
			)
			self.assertTrue((sec["5_bundle"] or {}).get("available"))
			self.assertTrue((sec["10_boq"] or {}).get("boq_matches_snapshot"))
			actions = (sec["14_available_approval_actions"] or {}).get("actions") or []
			self.assertGreaterEqual(len(actions), 4)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0300_after_snapshot_invalidated_raises(self) -> None:
		tn, _si_name, snap_name = self._ready_tender_with_snapshot("PUB0300-INV")
		try:
			ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor="Administrator")
			ConfigurationSnapshotService.invalidateConfigurationSnapshot(
				snap_name,
				"test invalidate for review",
				actor="Administrator",
			)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ApprovalReviewPackageService.getApprovalReviewPackage(tn, actor="Administrator")
			self.assertEqual(_last_msg_title(), APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED)
		finally:
			self._cleanup_tender(tn)
