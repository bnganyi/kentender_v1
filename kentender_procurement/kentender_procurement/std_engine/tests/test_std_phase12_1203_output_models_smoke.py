# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CURSOR-1203 — forms/DSM, BOQ, DOM, DEM, DCM smoke groups (Smoke Contract §22)."""

from __future__ import annotations

import frappe
from frappe.utils import parse_json

from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.tests.test_std_phase6_generation_engine import _Phase6Fixture


def _output_payload_dict(doc) -> dict:
	p = doc.get("output_payload")
	if p is None:
		return {}
	if isinstance(p, str):
		return parse_json(p) if p.strip() else {}
	return p


class TestStdEngineWorksFormsDsmTests(_Phase6Fixture):
	"""std_engine_works_forms_dsm_tests"""

	def test_section_iv_forms_surface_in_bundle_manifest(self):
		res = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		manifest = _output_payload_dict(doc)
		ids = {s["id"] for s in manifest.get("sections") or []}
		self.assertIn("section_iv_forms", ids, msg="Bundle must include Section IV forms (DSM source)")

	def test_dsm_read_only_with_rate_only_for_boq(self):
		res = generate_std_outputs(self.instance_code, scope="DSM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		self.assertTrue(pl.get("read_only_model"), msg="DSM must be read-only submission model")
		group = next(g for g in pl["groups"] if g["group_id"] == "priced_boq")
		row = group["fields"][0]
		self.assertFalse(row["quantity"]["editable"], msg="Supplier must not edit PE-owned quantity")
		self.assertTrue(row["rate"]["editable"], msg="Supplier rate entry required")


class TestStdEngineWorksBoqTests(_Phase6Fixture):
	"""std_engine_works_boq_tests"""

	def test_boq_definition_structured_for_instance(self):
		from kentender_procurement.std_engine.services.boq_instance_service import validate_boq_instance

		out = validate_boq_instance(self.instance_code, persist=False)
		self.assertTrue(out.get("is_valid"), msg=f"BOQ validation failed: {out}")


class TestStdEngineWorksDomTests(_Phase6Fixture):
	"""std_engine_works_dom_tests"""

	def test_dom_generated_without_evaluation_arithmetic_stage(self):
		res = generate_std_outputs(self.instance_code, scope="DOM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		raw = frappe.as_json(pl)
		self.assertNotIn("Arithmetic Correction", raw, msg="DOM must not carry evaluation arithmetic correction")
		self.assertIn("opening_fields", pl, msg="DOM must expose opening fields")


class TestStdEngineWorksDemTests(_Phase6Fixture):
	"""std_engine_works_dem_tests"""

	def test_dem_contains_arithmetic_correction_stage(self):
		res = generate_std_outputs(self.instance_code, scope="DEM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		stages = pl.get("stages") or []
		self.assertIn("Arithmetic Correction", stages, msg="DEM must include arithmetic correction stage")


class TestStdEngineWorksDcmTests(_Phase6Fixture):
	"""std_engine_works_dcm_tests"""

	def test_dcm_price_source_points_to_evaluated_boq_total(self):
		res = generate_std_outputs(self.instance_code, scope="DCM", actor="Administrator")
		doc = frappe.get_doc("STD Generated Output", {"output_code": res["outputs"][0]["output_code"]})
		pl = _output_payload_dict(doc)
		cf = pl["carry_forward"]["corrected_evaluated_contract_price"]
		self.assertIn("Evaluation/Award", cf["source_rule"])
		self.assertIn("raw_submitted_boq_total", cf["disallowed_sources"])
