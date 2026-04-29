# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CURSOR-1205 — std_engine_works_cross_module_tests + std_engine_works_negative_regression_tests."""

from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender, get_tender_std_binding
from kentender_procurement.std_engine.services.tender_contract_guard_service import (
	DENIAL_CODE_CONTRACT_SOURCE_MISMATCH,
	DENIAL_CODE_DCM_REQUIRED,
	WORKS_REQUIRED_CONTRACT_PRICE_SOURCE,
	create_contract_from_std,
	validate_contract_creation_inputs,
)
from kentender_procurement.std_engine.services.tender_evaluation_guard_service import (
	DENIAL_CODE_MANUAL_EVALUATION_BLOCKED,
	check_manual_evaluation_criteria_permission,
	create_manual_evaluation_criterion,
)
from kentender_procurement.std_engine.services.tender_opening_guard_service import (
	DENIAL_CODE_DOM_REQUIRED,
	DENIAL_CODE_MANUAL_OPENING_BLOCKED,
	check_manual_opening_field_permission,
	create_manual_opening_field,
	validate_opening_can_proceed,
)
from kentender_procurement.std_engine.services.tender_submission_guard_service import (
	DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED,
	check_manual_submission_requirement_permission,
)
from kentender_procurement.std_engine.tests.test_std_phase6_generation_engine import _Phase6Fixture
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestStdEngineWorksCrossModuleTests(_Phase7Fixture):
	"""std_engine_works_cross_module_tests"""

	def tearDown(self):
		frappe.db.delete("STD Tender Binding", {"tender_code": ("like", "TND-PH12-CM-%")})
		super().tearDown()

	def test_binding_reflects_outputs_not_current_until_ready(self):
		bind_std_instance_to_tender("TND-PH12-CM-1", self.instance_code, actor="Administrator")
		b = get_tender_std_binding("TND-PH12-CM-1")["binding"]
		self.assertTrue(b)
		self.assertEqual(0, int(b.get("std_outputs_current") or 0))

	def test_binding_carries_bundle_dsm_dom_dem_dcm_refs_when_ready(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-PH12-CM-2", self.instance_code, actor="Administrator")
		b = get_tender_std_binding("TND-PH12-CM-2")["binding"]
		self.assertEqual(1, int(b.get("std_outputs_current") or 0))
		for key in ("std_bundle_code", "std_dsm_code", "std_dom_code", "std_dem_code", "std_dcm_code"):
			self.assertTrue(b.get(key), msg=f"Missing binding ref {key}")

	def test_submission_manual_checklist_blocked_implies_dsm_governed_surface(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-PH12-CM-3", self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = check_manual_submission_requirement_permission("TND-PH12-CM-3", actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_MANUAL_SUBMISSION_BLOCKED, perm["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_opening_requires_dom_reference(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-PH12-CM-4", self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			frappe.db.set_value("STD Tender Binding", {"tender_code": "TND-PH12-CM-4"}, "std_dom_code", None, update_modified=False)
			v = validate_opening_can_proceed("TND-PH12-CM-4", actor="Administrator")
			self.assertFalse(v["allowed"])
			self.assertEqual(DENIAL_CODE_DOM_REQUIRED, v["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_contract_creation_requires_dcm_reference(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-PH12-CM-5", self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			frappe.db.set_value("STD Tender Binding", {"tender_code": "TND-PH12-CM-5"}, "std_dcm_code", None, update_modified=False)
			perm = validate_contract_creation_inputs("TND-PH12-CM-5", {}, actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_DCM_REQUIRED, perm["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old


class TestStdEngineWorksNegativeRegressionTests(_Phase6Fixture):
	"""std_engine_works_negative_regression_tests"""

	def test_manual_opening_field_denied_when_std_v2(self):
		# Reuse phase7-style binding on this instance via a dedicated tender row.
		tcode = "TND-PH12-NEG-OP"
		frappe.db.delete("STD Tender Binding", {"tender_code": tcode})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender(tcode, self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = check_manual_opening_field_permission(tcode, actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_MANUAL_OPENING_BLOCKED, perm["denial_code"])
			with self.assertRaises(frappe.ValidationError):
				create_manual_opening_field(tcode, {"label": "Manual open"}, actor="Administrator")
		finally:
			frappe.conf.std_engine_v2_enabled = old
			frappe.db.delete("STD Tender Binding", {"tender_code": tcode})

	def test_manual_evaluation_criterion_denied_when_std_v2(self):
		tcode = "TND-PH12-NEG-EV"
		frappe.db.delete("STD Tender Binding", {"tender_code": tcode})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender(tcode, self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = check_manual_evaluation_criteria_permission(tcode, actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_MANUAL_EVALUATION_BLOCKED, perm["denial_code"])
			with self.assertRaises(frappe.ValidationError):
				create_manual_evaluation_criterion(tcode, {"label": "Manual eval"}, actor="Administrator")
		finally:
			frappe.conf.std_engine_v2_enabled = old
			frappe.db.delete("STD Tender Binding", {"tender_code": tcode})

	def test_manual_contract_carry_forward_override_denied(self):
		tcode = "TND-PH12-NEG-CT"
		frappe.db.delete("STD Tender Binding", {"tender_code": tcode})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender(tcode, self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = validate_contract_creation_inputs(
				tcode,
				{"contract_price_source": "raw_submitted_boq_total"},
				actor="Administrator",
			)
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_CONTRACT_SOURCE_MISMATCH, perm["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old
			frappe.db.delete("STD Tender Binding", {"tender_code": tcode})

	def test_published_bundle_output_not_superseded_on_regeneration(self):
		r1 = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		bundle_code = r1["outputs"][0]["output_code"]
		transition_std_object("GENERATED_OUTPUT", bundle_code, "STD_OUTPUT_PUBLISH", "Administrator", context={"requires_confirmation": True})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		self.assertEqual("Published", frappe.db.get_value("STD Generated Output", bundle_code, "status"))

	def test_dcm_create_allowed_with_required_evaluated_price_source(self):
		tcode = "TND-PH12-NEG-DCMOK"
		frappe.db.delete("STD Tender Binding", {"tender_code": tcode})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender(tcode, self.instance_code, actor="Administrator")
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			resp = create_contract_from_std(
				tcode,
				{"contract_price_source": WORKS_REQUIRED_CONTRACT_PRICE_SOURCE},
				actor="Administrator",
			)
			self.assertTrue(resp.get("created"))
		finally:
			frappe.conf.std_engine_v2_enabled = old
			frappe.db.delete("STD Tender Binding", {"tender_code": tcode})
