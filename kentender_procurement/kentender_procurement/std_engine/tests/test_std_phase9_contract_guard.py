from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.tender_binding_service import bind_std_instance_to_tender
from kentender_procurement.std_engine.services.tender_contract_guard_service import (
	DENIAL_CODE_CONTRACT_SOURCE_MISMATCH,
	DENIAL_CODE_DCM_REQUIRED,
	WORKS_REQUIRED_CONTRACT_PRICE_SOURCE,
	create_contract_from_std,
	validate_contract_creation_inputs,
)
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR0905ContractGuard(_Phase7Fixture):
	def setUp(self):
		super().setUp()
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		bind_std_instance_to_tender("TND-0905-1", self.instance_code, actor="Administrator")

	def tearDown(self):
		frappe.db.delete("STD Tender Binding", {"tender_code": "TND-0905-1"})
		super().tearDown()

	def test_contract_creation_requires_dcm(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			frappe.db.set_value("STD Tender Binding", {"tender_code": "TND-0905-1"}, "std_dcm_code", None, update_modified=False)
			perm = validate_contract_creation_inputs("TND-0905-1", {}, actor="Administrator")
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_DCM_REQUIRED, perm["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_works_contract_source_mismatch_denied(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			perm = validate_contract_creation_inputs(
				"TND-0905-1",
				{"contract_price_source": "raw_submitted_boq_total"},
				actor="Administrator",
			)
			self.assertFalse(perm["allowed"])
			self.assertEqual(DENIAL_CODE_CONTRACT_SOURCE_MISMATCH, perm["denial_code"])
		finally:
			frappe.conf.std_engine_v2_enabled = old

	def test_contract_create_allowed_with_required_source(self):
		old = frappe.conf.get("std_engine_v2_enabled")
		frappe.conf.std_engine_v2_enabled = 1
		try:
			resp = create_contract_from_std(
				"TND-0905-1",
				{"contract_price_source": WORKS_REQUIRED_CONTRACT_PRICE_SOURCE},
				actor="Administrator",
			)
			self.assertTrue(resp["created"])
		finally:
			frappe.conf.std_engine_v2_enabled = old
