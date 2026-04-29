# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-CURSOR-1204 — bundle, readiness, addendum smoke groups."""

from __future__ import annotations

import frappe
from frappe.utils import parse_json

from kentender_procurement.std_engine.services.addendum_impact_service import analyze_std_addendum_impact
from kentender_procurement.std_engine.services.addendum_regeneration_service import regenerate_std_outputs_for_addendum
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.readiness_service import run_std_readiness
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object
from kentender_procurement.std_engine.tests.test_std_phase6_generation_engine import _Phase6Fixture
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


def _output_payload_dict(doc) -> dict:
	p = doc.get("output_payload")
	if p is None:
		return {}
	if isinstance(p, str):
		return parse_json(p) if p.strip() else {}
	return p


class TestStdEngineWorksBundleTests(_Phase6Fixture):
	"""std_engine_works_bundle_tests"""

	def test_bundle_generated_with_required_sections_and_preface_excluded(self):
		res = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		self.assertTrue(res.get("outputs"))
		code = res["outputs"][0]["output_code"]
		doc = frappe.get_doc("STD Generated Output", {"output_code": code})
		manifest = _output_payload_dict(doc)
		ids = {s["id"] for s in manifest.get("sections") or []}
		for required in (
			"issued_page",
			"invitation_to_tender",
			"section_i_itt",
			"section_ii_tds",
			"section_iii_evaluation",
			"section_iv_forms",
			"section_v_boq",
		):
			self.assertIn(required, ids, msg=f"bundle missing section id={required}")
		self.assertIn("preface", {x["id"] for x in manifest.get("excluded_from_supplier_bundle") or []})

	def test_published_bundle_not_superseded_on_regeneration(self):
		r1 = generate_std_outputs(self.instance_code, scope="Bundle", actor="Administrator")
		bundle_code = r1["outputs"][0]["output_code"]
		transition_std_object("GENERATED_OUTPUT", bundle_code, "STD_OUTPUT_PUBLISH", "Administrator", context={"requires_confirmation": True})
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		self.assertEqual("Published", frappe.db.get_value("STD Generated Output", bundle_code, "status"))


class TestStdEngineWorksReadinessTests(_Phase7Fixture):
	"""std_engine_works_readiness_tests"""

	def test_complete_instance_readiness_passes(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Ready", res["status"], msg=f"Unexpected findings: {res.get('findings')}")

	def test_missing_generated_outputs_blocks_readiness(self):
		generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		dem = frappe.db.get_value(
			"STD Generated Output",
			{"instance_code": self.instance_code, "output_type": "DEM", "status": "Current"},
			"name",
		)
		frappe.delete_doc("STD Generated Output", dem, force=True, ignore_permissions=True)
		res = run_std_readiness("STD_INSTANCE", self.instance_code, actor="Administrator")
		self.assertEqual("Blocked", res["status"])
		self.assertTrue(any("DEM" in f["rule_code"] for f in res["findings"]))

	def test_manual_readiness_field_mutation_denied(self):
		inst = frappe.get_doc("STD Instance", {"instance_code": self.instance_code})
		inst.reload()
		with self.assertRaises(frappe.ValidationError):
			inst.readiness_status = "Ready"
			inst.save(ignore_permissions=True)


class TestStdEngineWorksAddendumTests(_Phase7Fixture):
	"""std_engine_works_addendum_tests"""

	def test_boq_addendum_impact_requires_regeneration(self):
		impact = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-PH12-BOQ",
			[{"change_type": "BOQ_QUANTITY_CHANGE", "field": "quantity"}],
			"Administrator",
		)
		self.assertEqual("Regeneration Required", impact["status"])
		self.assertEqual({"Bundle", "DSM", "DEM", "DCM"}, set(impact["impacted_output_types"]))

	def test_regeneration_after_deadline_change_supersedes_prior_outputs(self):
		base = generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		bundle_old = next(x["output_code"] for x in base["outputs"] if x["output_type"] == "Bundle")
		impact = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-PH12-DL",
			[{"change_type": "SUBMISSION_DEADLINE_CHANGE"}],
			"Administrator",
		)
		out = regenerate_std_outputs_for_addendum(impact["impact_analysis_code"], "Administrator")
		self.assertEqual("Regenerated", out["status"])
		self.assertEqual("Superseded", frappe.db.get_value("STD Generated Output", bundle_old, "status"))
		new_bundle = next(x["output_code"] for x in out["outputs"] if x["output_type"] == "Bundle")
		row = frappe.db.get_value(
			"STD Generated Output",
			{"output_code": new_bundle},
			["source_addendum_code", "supersedes_output_code"],
			as_dict=True,
		)
		self.assertEqual("ADD-PH12-DL", row.source_addendum_code)
		self.assertEqual(bundle_old, row.supersedes_output_code)
