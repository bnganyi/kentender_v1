# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0700 — ``EvidencePackageService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_evidence_package_0700
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
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EXPORT_FORMAT_AUDIT_LOG,
	EXPORT_FORMAT_JSON_MANIFEST,
	EvidencePackageService,
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


class TestPubEvidencePackage0700(IntegrationTestCase):
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

	def _cleanup_user(self, email: str) -> None:
		if frappe.db.exists("User", email):
			frappe.delete_doc("User", email, force=True, ignore_permissions=True)

	def _minimal_tender(self, *, ref: str) -> str:
		doc = frappe.new_doc("Procurement Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = f"PUB-0700 {ref}"
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

	def _ready_instance_no_config_snapshot(self, ref: str) -> tuple[str, str]:
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
			structured_text="PUB-0700 requirement.",
			requirement_status="Complete",
			attachment_required=False,
			attachment_status="Not Required",
			ignore_publication_lock=True,
		)
		self._ensure_minimum_boq(si.name)
		self._publish_all_outputs(si.name)
		self.assertEqual(StdInstanceReadinessService.evaluate(si.name, persist=False)["status"], "Ready")
		return tn, si.name

	def _approved_locked_fixture(self, ref: str) -> tuple[str, str]:
		tn, si = self._ready_instance_no_config_snapshot(ref)
		ConfigurationSnapshotService.createConfigurationSnapshot(tn, actor="Administrator")
		ApprovalDecisionService.approveForPublication(tn, {"decision_note": "ok"}, actor="Administrator")
		return tn, si

	def test_pub_0700_validate_readiness_gate_ok(self) -> None:
		tn, _si = self._ready_instance_no_config_snapshot("PUB0700-RG")
		try:
			res = EvidencePackageService.validate_for_readiness_gate(tn)
			self.assertTrue(res.get("ok"), msg=str(res.get("missing")))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0700_validate_publication_requires_configuration_snapshot(self) -> None:
		tn, _si = self._ready_instance_no_config_snapshot("PUB0700-NOCFG")
		try:
			res = EvidencePackageService.validateEvidencePackage(tn)
			self.assertFalse(res.get("ok"))
			self.assertIn("configuration_snapshot", res.get("missing") or [])
		finally:
			self._cleanup_tender(tn)

	def test_pub_0700_validate_publication_ok_before_publish(self) -> None:
		tn, _si = self._approved_locked_fixture("PUB0700-PUBV")
		try:
			res = EvidencePackageService.validateEvidencePackage(tn)
			self.assertTrue(res.get("ok"), msg=str(res.get("missing")))
			self.assertTrue((res.get("fingerprint") or {}).get("approval_decision"))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0700_assemble_returns_code(self) -> None:
		tn, _si = self._approved_locked_fixture("PUB0700-ASM")
		try:
			env = EvidencePackageService.assembleEvidencePackage(tn, actor_or_system="Administrator")
			self.assertTrue(env.get("ok"))
			self.assertTrue((env.get("evidence_package_code") or "").startswith("EVIDENCE|"))
		finally:
			self._cleanup_tender(tn)

	def test_pub_0700_export_after_publish(self) -> None:
		tn, _si = self._approved_locked_fixture("PUB0700-EXP")
		try:
			PublicationTransactionService.publishTender(tn, actor="Administrator")
			frappe.db.commit()
			m = EvidencePackageService.exportEvidencePackage(
				tn,
				EXPORT_FORMAT_JSON_MANIFEST,
				actor="Administrator",
			)
			self.assertTrue(m.get("ok"))
			self.assertIn("tender_code", m.get("data") or {})
			a = EvidencePackageService.exportEvidencePackage(
				tn,
				EXPORT_FORMAT_AUDIT_LOG,
				actor="Administrator",
			)
			self.assertTrue(a.get("ok"))
			self.assertIsInstance((a.get("data") or {}).get("events"), list)
		finally:
			self._cleanup_tender(tn)

	def test_pub_0700_export_denied_without_privileged_role(self) -> None:
		email = "pub0700_norole@example.com"
		tn, _si = self._approved_locked_fixture("PUB0700-DENY")
		try:
			if not frappe.db.exists("User", email):
				u = frappe.new_doc("User")
				u.email = email
				u.first_name = "Pub"
				u.last_name = "0700"
				u.send_welcome_email = 0
				u.append("roles", {"role": "Procurement Assistant"})
				u.insert(ignore_permissions=True)
			frappe.set_user(email)
			with self.assertRaises(frappe.ValidationError):
				EvidencePackageService.exportEvidencePackage(
					tn,
					EXPORT_FORMAT_JSON_MANIFEST,
					actor=email,
				)
		finally:
			self._cleanup_tender(tn)
			self._cleanup_user(email)
