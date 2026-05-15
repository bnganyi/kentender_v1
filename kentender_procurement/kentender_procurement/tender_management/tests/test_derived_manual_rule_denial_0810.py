# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0810 — ``ManualRuleDenialService``.

Run::

	bench --site kentender.midas.com run-tests --app kentender_procurement \\
		--module kentender_procurement.tender_management.tests.test_derived_manual_rule_denial_0810
"""

from __future__ import annotations

import json
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial import (
	BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION,
	CONTRACT_BINDING_VIOLATION,
	MANUAL_EVALUATION_CRITERIA_DENIED,
	ManualRuleDenialService,
	MANUAL_OPENING_EVALUATION_FIELD_DENIED,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.seeds.std_template_governance_seed import (
	seed_std_template_governance_for_existing_works_poc,
)
from kentender_procurement.tender_management.services.std_template_loader import (
	TEMPLATE_CODE,
	upsert_std_template,
)
from kentender_procurement.tender_management.std_instance.binding import TenderStdBindingService
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)


def _last_msg_title() -> str:
	log = frappe.get_message_log()
	return (log[-1].get("title") or "").strip() if log else ""


class TestDerivedManualRuleDenial0810(IntegrationTestCase):
	def setUp(self) -> None:
		super().setUp()
		frappe.set_user("Administrator")
		frappe.clear_messages()
		upsert_std_template()
		seed_std_template_governance_for_existing_works_poc(force_mode="active")

	def tearDown(self) -> None:
		frappe.set_user("Administrator")
		super().tearDown()

	def _cleanup_tender(self, tender_name: str) -> None:
		for name in frappe.get_all(
			"Tender STD Instance",
			filters={"tm2_tender": tender_name},
			pluck="name",
		):
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

	def test_derived_0810_submission_denies_dsm_prohibited_key(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				{
					"std_inst": "STDINST-X",
					"requirements": [
						{
							"requirement_code": "R1",
							"requirement_type": "Form",
							"source_trace": {"source_type": "SystemRule"},
							"ranking": [],
						},
					],
				}
			)
		self.assertEqual(_last_msg_title(), MANUAL_SUBMISSION_REQUIREMENT_DENIED)

	def test_derived_0810_submission_denies_manual_injection_key(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				{"manual_submission_requirement": True},
			)
		self.assertEqual(_last_msg_title(), MANUAL_SUBMISSION_REQUIREMENT_DENIED)

	def test_derived_0810_submission_denies_missing_source_trace(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_submission_requirement(
				[
					{
						"requirement_code": "R1",
						"requirement_type": "Form",
						"label": "X",
					},
				],
			)
		self.assertEqual(_last_msg_title(), MANUAL_SUBMISSION_REQUIREMENT_DENIED)

	def test_derived_0810_opening_denies_boq_arithmetic_stage(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_opening_evaluation_field(
				[{"stage_type": "BOQArithmetic", "label": "bad"}],
			)
		self.assertEqual(_last_msg_title(), BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION)

	def test_derived_0810_opening_denies_dom_prohibited_key(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_opening_evaluation_field(
				{"register": {"evaluation_ranking": {}}},
			)
		self.assertEqual(_last_msg_title(), MANUAL_OPENING_EVALUATION_FIELD_DENIED)

	def test_derived_0810_opening_validate_payload_matches_assert_path(self) -> None:
		bad = ManualRuleDenialService.validate_opening_register_payload(
			{"arithmetic_correction": {"applied": True}},
		)
		self.assertFalse(bad.get("ok"))
		self.assertEqual(bad.get("denial_code"), DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value)
		good = ManualRuleDenialService.validate_opening_register_payload({})
		self.assertTrue(good.get("ok"), good)

	def test_derived_0810_evaluation_denies_manual_criteria_key(self) -> None:
		frappe.clear_messages()
		with self.assertRaises(frappe.ValidationError):
			ManualRuleDenialService.assert_no_manual_evaluation_criteria(
				{"tiers": {"manual_criteria": True}},
			)
		self.assertEqual(_last_msg_title(), MANUAL_EVALUATION_CRITERIA_DENIED)

	def test_derived_0810_contract_denies_divergence(self) -> None:
		doc = frappe.new_doc("TM2 Tender")
		doc.std_template = TEMPLATE_CODE
		doc.tender_title = "DERIVED-0810 Contract"
		doc.tender_reference = "DERIVED0810-CON"
		doc.insert(ignore_permissions=True)
		try:
			si = TenderStdBindingService.create_std_instance_for_tm2_tender(
				doc.name,
				ignore_permissions=True,
				record_template_usage=False,
			)
			WorksBoqCompletionService.save_boq(si.name, self._minimal_valid_boq_payload())
			dcm = StdInstanceGeneratedOutputService.generate_dcm(si.name)
			pub = StdInstanceGeneratedOutputService.publish_output(dcm.name)
			content = pub.get("content_json")
			if isinstance(content, str):
				content = json.loads(content)
			self.assertIsInstance(content, dict)
			terms = content.get("contract_terms") or []
			self.assertTrue(isinstance(terms, list) and terms)
			locked = next(
				(t for t in terms if isinstance(t, dict) and not t.get("editable_in_contract")),
				None,
			)
			self.assertTrue(locked)
			tc = (locked.get("term_code") or "").strip()
			self.assertTrue(tc)

			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ManualRuleDenialService.assert_no_contract_divergence(
					{
						"std_inst": si.name,
						"contract_terms": [
							{"term_code": tc, "value": {"tampered": True}},
						],
					},
					pub.name,
				)
			self.assertEqual(_last_msg_title(), CONTRACT_BINDING_VIOLATION)

			frappe.clear_messages()
			with self.assertRaises(frappe.ValidationError):
				ManualRuleDenialService.assert_no_contract_divergence(
					{"override_dcm": True},
					pub.name,
				)
			self.assertEqual(_last_msg_title(), CONTRACT_BINDING_VIOLATION)

			ManualRuleDenialService.assert_no_contract_divergence(
				{
					"std_inst": si.name,
					"contract_terms": [
						{"term_code": tc, "value": locked.get("value")},
					],
				},
				pub.name,
			)
		finally:
			self._cleanup_tender(doc.name)

	def test_derived_0810_denial_emits_audit(self) -> None:
		with patch(
			"kentender_procurement.tender_management.derived_models.consumption.manual_rule_denial.emit_std_instance_event"
		) as m:
			with self.assertRaises(frappe.ValidationError):
				ManualRuleDenialService.assert_no_manual_submission_requirement(
					{"manual_requirement": {"x": 1}},
				)
			m.assert_called_once()
			args, kwargs = m.call_args
			self.assertEqual(args[0], EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION)
			self.assertEqual(kwargs.get("details", {}).get("denial_code"), MANUAL_SUBMISSION_REQUIREMENT_DENIED)
