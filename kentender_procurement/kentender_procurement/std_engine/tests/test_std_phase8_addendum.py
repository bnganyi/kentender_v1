from __future__ import annotations

import frappe

from kentender_procurement.std_engine.services.addendum_impact_service import analyze_std_addendum_impact
from kentender_procurement.std_engine.services.addendum_regeneration_service import regenerate_std_outputs_for_addendum
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.tests.test_std_phase7_readiness import _Phase7Fixture


class TestSTDCURSOR0801AddendumImpactAnalyzer(_Phase7Fixture):
	def test_boq_quantity_change_requires_bundle_dsm_dem_dcm(self):
		res = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-0801-BOQ",
			[{"change_type": "BOQ_QUANTITY_CHANGE", "field": "quantity"}],
			"Administrator",
		)
		self.assertEqual("Regeneration Required", res["status"])
		self.assertEqual({"Bundle", "DSM", "DEM", "DCM"}, set(res["impacted_output_types"]))
		self.assertTrue(res["requires_acknowledgement"])
		self.assertTrue(res["requires_deadline_review"])

	def test_deadline_change_requires_bundle_dsm_dom(self):
		res = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-0801-DL",
			[{"change_type": "SUBMISSION_DEADLINE_CHANGE"}],
			"Administrator",
		)
		self.assertEqual({"Bundle", "DSM", "DOM"}, set(res["impacted_output_types"]))

	def test_impact_analysis_auditable(self):
		res = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-0801-AUD",
			[{"change_type": "SCC_VALUE_CHANGE"}],
			"Administrator",
		)
		self.assertTrue(
			frappe.db.exists(
				"STD Audit Event",
				{"event_type": "ADDENDUM_IMPACT_ANALYZED", "object_code": res["impact_analysis_code"]},
			)
		)


class TestSTDCURSOR0802AddendumRegeneration(_Phase7Fixture):
	def test_regenerates_affected_outputs_and_preserves_history(self):
		base = generate_std_outputs(self.instance_code, scope="all", actor="Administrator")
		bundle_old = next(x["output_code"] for x in base["outputs"] if x["output_type"] == "Bundle")
		impact = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-0802-R1",
			[{"change_type": "SUBMISSION_DEADLINE_CHANGE"}],
			"Administrator",
		)
		out = regenerate_std_outputs_for_addendum(impact["impact_analysis_code"], "Administrator")
		self.assertEqual("Regenerated", out["status"])
		new_types = {x["output_type"] for x in out["outputs"]}
		self.assertEqual({"Bundle", "DSM", "DOM"}, new_types)
		self.assertEqual("Superseded", frappe.db.get_value("STD Generated Output", {"output_code": bundle_old}, "status"))
		new_bundle = next(x["output_code"] for x in out["outputs"] if x["output_type"] == "Bundle")
		row = frappe.db.get_value(
			"STD Generated Output",
			{"output_code": new_bundle},
			["source_addendum_code", "supersedes_output_code"],
			as_dict=True,
		)
		self.assertEqual("ADD-0802-R1", row.source_addendum_code)
		self.assertEqual(bundle_old, row.supersedes_output_code)

	def test_requires_analysis_approval_or_regen_required(self):
		impact = analyze_std_addendum_impact(
			self.instance_code,
			"ADD-0802-BLK",
			[{"change_type": "SCC_VALUE_CHANGE"}],
			"Administrator",
		)
		doc = frappe.get_doc("STD Addendum Impact Analysis", {"impact_analysis_code": impact["impact_analysis_code"]})
		frappe.flags.std_transition_service_context = True
		try:
			doc.status = "Analysis Complete"
			doc.save(ignore_permissions=True)
		finally:
			frappe.flags.std_transition_service_context = False
		with self.assertRaises(frappe.ValidationError):
			regenerate_std_outputs_for_addendum(impact["impact_analysis_code"], "Administrator")
