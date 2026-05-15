# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""SEC-0820 — downstream control smoke tests (`SEC-SMOKE-DOWN-001` … `008`).

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_sec_smoke_downstream_controls_0820
"""

from __future__ import annotations

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import now_datetime

from kentender_procurement.tender_management.derived_models.common.versioning import (
	DerivedOutputVersioningService,
)
from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION,
	CONTRACT_BINDING_VIOLATION,
	MANUAL_EVALUATION_CRITERIA_DENIED,
	ManualRuleDenialService,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
)
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
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


def _last_title() -> str:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else ""


class TestSecSmokeDownstreamControls0820(IntegrationTestCase):
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

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
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
				frappe.delete_doc(
					"Tender STD Instance Snapshot",
					snap_name,
					force=True,
					ignore_permissions=True,
				)
			for out_name in frappe.get_all(
				"Tender STD Generated Output",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Generated Output",
					out_name,
					force=True,
					ignore_permissions=True,
				)
			for boq_name in frappe.get_all(
				"Tender STD Instance BOQ",
				filters={"tender_std_instance": name},
				pluck="name",
			):
				frappe.delete_doc(
					"Tender STD Instance BOQ",
					boq_name,
					force=True,
					ignore_permissions=True,
				)
			frappe.delete_doc("Tender STD Instance", name, force=True, ignore_permissions=True)
		if frappe.db.exists("TM2 Tender", tender_name):
			frappe.delete_doc("TM2 Tender", tender_name, force=True, ignore_permissions=True)

	def _minimal_valid_boq_payload(self) -> dict:
		return {
			"header": {"currency": "USD"},
			"bills": [
				{
					"bill_number": "B1",
					"bill_title": "Preliminaries",
					"bill_type": "Standard",
					"order_index": 0,
					"items": [
						{
							"item_number": "1.1",
							"description": "Site clearance",
							"unit": "m2",
							"quantity": 100,
							"item_type": "Normal",
							"supplier_input_mode": "Rate Only",
						},
					],
				},
			],
		}

	def _final_snapshot(self, si_name: str, tender: str) -> str:
		inst = frappe.get_doc("Tender STD Instance", si_name)
		snap = frappe.new_doc("Tender STD Instance Snapshot")
		snap.tender_std_instance = si_name
		snap.tm2_tender = tender
		snap.snapshot_type = "Configuration"
		snap.snapshot_reason = "SEC-0820"
		snap.snapshot_status = "Final"
		snap.source_template_version_code = inst.template_version_code or "TV"
		snap.parameter_values_hash = "pv"
		snap.works_requirements_hash = "wr"
		snap.attachments_hash = "at"
		snap.boq_hash = "bq"
		snap.complete_instance_hash = "ci"
		snap.created_by = frappe.session.user
		snap.created_at = now_datetime()
		snap.insert(ignore_permissions=True)
		return snap.name

	def test_sec_smoke_down_001_submission_consumes_dsm_allowed(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "SEC-0820 DOWN-001"
		doc.tender_reference = "SEC0820-DOWN-001"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dsm = StdInstanceGeneratedOutputService.generate_dsm(si.name)
			StdInstanceGeneratedOutputService.publish_output(dsm.name)
			res = OutputConsumptionService.validate_consumption(dsm.name, "Submission", None)
			self.assertTrue(res.get("allowed"))
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)

	def test_sec_smoke_down_002_submission_manual_requirement_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				{"manual_submission_requirement": "ad-hoc"},
			)
		self.assertEqual(_last_title(), MANUAL_SUBMISSION_REQUIREMENT_DENIED)

	def test_sec_smoke_down_003_opening_consumes_dom_allowed(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "SEC-0820 DOWN-003"
		doc.tender_reference = "SEC0820-DOWN-003"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dom = StdInstanceGeneratedOutputService.generate_dom(si.name)
			StdInstanceGeneratedOutputService.publish_output(dom.name)
			res = OutputConsumptionService.validate_consumption(dom.name, "Opening", None)
			self.assertTrue(res.get("allowed"))
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)

	def test_sec_smoke_down_004_opening_arithmetic_correction_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_opening_evaluation_field(
				{"arithmetic_correction": {"applied": True}},
			)
		self.assertEqual(_last_title(), BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION)

	def test_sec_smoke_down_005_evaluation_consumes_dem_allowed(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "SEC-0820 DOWN-005"
		doc.tender_reference = "SEC0820-DOWN-005"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dem = StdInstanceGeneratedOutputService.generate_dem(si.name)
			StdInstanceGeneratedOutputService.publish_output(dem.name)
			res = OutputConsumptionService.validate_consumption(dem.name, "Evaluation", None)
			self.assertTrue(res.get("allowed"))
			self.assertEqual(res.get("output_status"), "Published")
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)

	def test_sec_smoke_down_006_evaluation_manual_criteria_denied(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_evaluation_criteria({"manual_criteria": {"x": 1}})
		self.assertEqual(_last_title(), MANUAL_EVALUATION_CRITERIA_DENIED)

	def test_sec_smoke_down_007_contract_consumes_dcm_allowed(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "SEC-0820 DOWN-007"
		doc.tender_reference = "SEC0820-DOWN-007"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			snap = self._final_snapshot(si.name, doc.name)
			dcm = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			DerivedOutputVersioningService.markCurrent(dcm.name)
			pub = DerivedOutputVersioningService.markPublished(dcm.name, snapshot_code=snap)
			res = OutputConsumptionService.validate_consumption(pub.name, "Contract", None)
			self.assertTrue(res.get("allowed"))
			self.assertEqual(res.get("snapshot_code"), snap)
			self.assertEqual(res.get("blockers"), [])
		finally:
			self._cleanup_tender(doc.name)

	def test_sec_smoke_down_008_contract_override_dcm_denied(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "SEC-0820 DOWN-008"
		doc.tender_reference = "SEC0820-DOWN-008"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			snap = self._final_snapshot(si.name, doc.name)
			dcm = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			DerivedOutputVersioningService.markCurrent(dcm.name)
			pub = DerivedOutputVersioningService.markPublished(dcm.name, snapshot_code=snap)
			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ManualRuleDenialService.assert_no_contract_divergence(
					{"override_dcm": True},
					pub.name,
				)
			self.assertEqual(_last_title(), CONTRACT_BINDING_VIOLATION)
		finally:
			self._cleanup_tender(doc.name)
