# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0110 — ``PublicationReadinessService`` (tender-scope readiness).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_pub_readiness_service_0110
"""

from __future__ import annotations

from unittest.mock import patch

import frappe

from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.security.authorization.action_authorization_registry import (
	spec_for_action,
)
from kentender_procurement.tender_management.services.bind_tender_std_instance import bind_tender_std_instance
from kentender_procurement.tender_management.services.create_tender_from_package import create_tender_from_package
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import canonical_tm2_tender_code
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.boq import StdInstanceBoqService
from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
)
from kentender_procurement.tender_management.std_instance.readiness import (
	StdInstanceReadinessService,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	StdInstanceWorksRequirementService,
)
from kentender_procurement.tender_management.tender_publication.evidence.evidence_package import (
	EvidencePackageService,
)
from kentender_procurement.tender_management.tender_publication.readiness import (
	publication_readiness as pub_read_mod,
)
from kentender_procurement.tender_management.tender_publication.readiness.publication_readiness import (
	PublicationReadinessService,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	PUBLICATION_READINESS_GATE_FAILED,
)
from kentender_procurement.tender_management.tests.test_p4_01_create_tender_from_package import (
	_P401Tm2Cleanup,
)


def _last_msg_title() -> str | None:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else None


class TestPubReadinessService0110(_P401Tm2Cleanup):
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

	def _mk_released_tm2(self) -> tuple[str, str]:
		"""Return ``(tm2_name, tender_code)`` for a released-package TM2 tender (Draft, bound separately)."""
		frappe.db.set_value(
			"STD Template",
			TEMPLATE_CODE,
			{"allowed_for_tender_creation": 1, "lifecycle_status": "Active"},
		)
		plan = self._mk_plan()
		frappe.db.set_value("Procurement Plan", plan.name, "status", "Approved")
		tpl = self._mk_template()
		pkg = self._mk_package(plan.name, tpl.name)
		self._add_seed_budget_line_and_demand(pkg.name)
		frappe.db.set_value("Procurement Package", pkg.name, "status", "Ready for Tender")
		spec_c = spec_for_action("TND2_CREATE_FROM_PACKAGE")
		self.assertIsNotNone(spec_c)
		assert spec_c is not None
		pc = frappe.db.get_value("Procurement Package", pkg.name, "package_code") or pkg.name
		out = create_tender_from_package(
			"Administrator",
			pc,
			context={"granted_permissions": [spec_c.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		tm2_name = str(out.get("tm2_tender") or "")
		tcode = str(out.get("tender_code") or "")
		self.assertTrue(tm2_name)
		self.assertTrue(tcode)
		self.addCleanup(self._cleanup_tm2, tm2_name)
		return tm2_name, tcode

	def _bind_std(self, tcode: str) -> str:
		ver, prof = TenderStdBindingService._codes_from_std_template(TEMPLATE_CODE)
		spec_b = spec_for_action("TND2_BIND_STD")
		self.assertIsNotNone(spec_b)
		assert spec_b is not None
		out = bind_tender_std_instance(
			"Administrator",
			tcode,
			ver,
			prof,
			context={"granted_permissions": [spec_b.required_permission]},
		)
		self.assertTrue(out.get("ok"), out)
		si = str(out.get("tender_std_instance") or "")
		self.assertTrue(si)
		return si

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
		from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance

		existing = get_boq_for_instance(instance_name)
		if existing:
			boq = frappe.get_doc("Tender STD Instance BOQ", existing.name)
		else:
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

	def _finalize_planning_release_for_tm2(self, tm2_name: str) -> None:
		"""Mark linked package **Released to Tender** and stamp a release code (readiness §6.1)."""
		pkg = (frappe.db.get_value("TM2 Tender", tm2_name, "procurement_package") or "").strip()
		if pkg and frappe.db.exists("Procurement Package", pkg):
			frappe.db.set_value("Procurement Package", pkg, "status", "Released to Tender", update_modified=False)
		frappe.db.set_value(
			"TM2 Tender",
			tm2_name,
			{
				"source_package_code": "REL-PUB0110-TEST",
				"std_template": TEMPLATE_CODE,
			},
			update_modified=False,
		)

	def test_pub_0110_missing_planning_lineage_blocks(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.tender_title = "PUB-0110 NOREL"
		doc.tender_reference = "PUB0110-NOREL"
		doc.procurement_category = "Works"
		doc.procuring_entity_code = "MOH"
		doc.fiscal_year = "2026"
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.addCleanup(self._cleanup_tm2, doc.name)
		tcode = canonical_tm2_tender_code(doc)
		res = PublicationReadinessService.runReadiness(doc.name, actor="Administrator")
		self.assertEqual(res["status"], "Blocked")
		codes = {f["code"] for f in res["findings"]}
		self.assertIn("RELEASE_RECORD_MISSING", codes)
		self.assertIn("STD_BINDING_MISSING", codes)
		latest = PublicationReadinessService.getLatestReadiness(tcode)
		self.assertEqual(latest["status"], "Blocked")

	def test_pub_0110_package_not_released_blocks(self) -> None:
		row = frappe.db.sql("select name from `tabProcurement Package` limit 1", as_dict=True)
		if not row:
			self.skipTest("No Procurement Package row in site DB.")
		pkg = row[0]["name"]
		prev = frappe.db.get_value("Procurement Package", pkg, "status")
		doc = frappe.new_doc("TM2 Tender")
		doc.tender_title = "PUB-0110 NOTREL"
		doc.tender_reference = "PUB0110-NOTREL"
		doc.procurement_category = "Works"
		doc.procuring_entity_code = "MOH"
		doc.fiscal_year = "2026"
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.addCleanup(self._cleanup_tm2, doc.name)
		tcode = canonical_tm2_tender_code(doc)
		try:
			frappe.db.set_value("Procurement Package", pkg, "status", "Draft")
			frappe.db.set_value("TM2 Tender", doc.name, "procurement_package", pkg)
			frappe.db.set_value("TM2 Tender", doc.name, "source_package_code", "")
			res = PublicationReadinessService.runReadiness(doc.name, actor="Administrator")
			self.assertEqual(res["status"], "Blocked")
			self.assertIn("RELEASE_RECORD_MISSING", {f["code"] for f in res["findings"]})
		finally:
			if prev:
				frappe.db.set_value("Procurement Package", pkg, "status", prev)

	def test_pub_0110_stale_dem_blocks(self) -> None:
		_tm2, tcode = self._mk_released_tm2()
		si = self._bind_std(tcode)
		try:
			self._finalize_planning_release_for_tm2(_tm2)
			StdInstanceParameterService.set_parameter_value(
				si,
				"submission_deadline",
				"2026-12-31",
				ignore_publication_lock=True,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si,
				"WR-COMP-001",
				structured_text="PUB-0110 requirement.",
				requirement_status="Complete",
				attachment_required=False,
				attachment_status="Not Required",
				ignore_publication_lock=True,
			)
			self._ensure_minimum_boq(si)
			self._publish_all_outputs(si)
			self.assertEqual(StdInstanceReadinessService.evaluate(si, persist=False)["status"], "Ready")
			StdInstanceGeneratedOutputService.mark_output_stale(si, output_type="DEM")
			res = PublicationReadinessService.runReadiness(tcode, actor="Administrator")
			self.assertEqual(res["status"], "Blocked")
			self.assertIn("DEM_NOT_CURRENT", {f["code"] for f in res["findings"]})
		finally:
			pass

	def test_pub_0110_ready_when_lineage_and_outputs_ok(self) -> None:
		_tm2, tcode = self._mk_released_tm2()
		si = self._bind_std(tcode)
		try:
			self._finalize_planning_release_for_tm2(_tm2)
			StdInstanceParameterService.set_parameter_value(
				si,
				"submission_deadline",
				"2026-12-31",
				ignore_publication_lock=True,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si,
				"WR-COMP-001",
				structured_text="PUB-0110 requirement.",
				requirement_status="Complete",
				attachment_required=False,
				attachment_status="Not Required",
				ignore_publication_lock=True,
			)
			self._ensure_minimum_boq(si)
			self._publish_all_outputs(si)
			res = PublicationReadinessService.runReadiness(tcode, actor="Administrator")
			self.assertEqual(res["status"], "Ready")
			self.assertEqual(res["findings"], [])
			PublicationReadinessService.assertReadyForApproval(tcode)
			PublicationReadinessService.assertReadyForPublication(tcode)
		finally:
			pass

	def test_pub_0110_assert_raises_when_blocked(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.tender_title = "PUB-0110 ASSERT"
		doc.tender_reference = "PUB0110-ASSERT"
		doc.procurement_category = "Works"
		doc.procuring_entity_code = "MOH"
		doc.fiscal_year = "2026"
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.addCleanup(self._cleanup_tm2, doc.name)
		tcode = canonical_tm2_tender_code(doc)
		try:
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				PublicationReadinessService.assertReadyForApproval(tcode)
			self.assertEqual(_last_msg_title(), PUBLICATION_READINESS_GATE_FAILED)
		finally:
			pass

	def test_pub_0110_evidence_gate_failure(self) -> None:
		_tm2, tcode = self._mk_released_tm2()
		si = self._bind_std(tcode)
		try:
			self._finalize_planning_release_for_tm2(_tm2)
			StdInstanceParameterService.set_parameter_value(
				si,
				"submission_deadline",
				"2026-12-31",
				ignore_publication_lock=True,
			)
			StdInstanceWorksRequirementService.set_works_requirement(
				si,
				"WR-COMP-001",
				structured_text="PUB-0110 requirement.",
				requirement_status="Complete",
				attachment_required=False,
				attachment_status="Not Required",
				ignore_publication_lock=True,
			)
			self._ensure_minimum_boq(si)
			self._publish_all_outputs(si)
			with patch.object(
				EvidencePackageService,
				"validate_for_readiness_gate",
				return_value={"ok": False, "reason": "fixture"},
			):
				res = PublicationReadinessService.runReadiness(tcode, actor="Administrator")
			self.assertEqual(res["status"], "Blocked")
			self.assertIn("EVIDENCE_PACKAGE_FAILED", {f["code"] for f in res["findings"]})
		finally:
			pass

	def test_pub_0110_get_latest_not_run(self) -> None:
		pub_read_mod.clear_publication_readiness_cache()
		doc = frappe.new_doc("TM2 Tender")
		doc.tender_title = "PUB-0110 NOTRUN"
		doc.tender_reference = "PUB0110-NOTRUN"
		doc.procurement_category = "Works"
		doc.procuring_entity_code = "MOH"
		doc.fiscal_year = "2026"
		doc.insert(ignore_permissions=True, ignore_mandatory=True)
		self.addCleanup(self._cleanup_tm2, doc.name)
		tcode = canonical_tm2_tender_code(doc)
		res = PublicationReadinessService.getLatestReadiness(tcode)
		self.assertEqual(res["status"], "Not Run")
		self.assertEqual(res["findings"], [])
