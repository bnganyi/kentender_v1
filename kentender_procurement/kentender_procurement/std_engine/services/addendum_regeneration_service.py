from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.generation_job_service import generate_std_outputs
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object


@frappe.whitelist()
def regenerate_std_outputs_for_addendum(impact_analysis_code: str, actor: str | None = None) -> dict[str, Any]:
	"""STD-CURSOR-0802: regenerate only impacted outputs for approved/addendum-required analysis."""
	actor = actor or frappe.session.user
	name = frappe.db.get_value("STD Addendum Impact Analysis", {"impact_analysis_code": impact_analysis_code}, "name")
	if not name:
		frappe.throw(_("Impact analysis not found."), title=_("Addendum regeneration"))
	impact = frappe.get_doc("STD Addendum Impact Analysis", name)
	if impact.status not in {"Approved", "Regeneration Required"}:
		frappe.throw(_("Impact analysis must be Approved or Regeneration Required before regeneration."), title=_("Addendum regeneration"))
	affected = impact.impacted_output_types_json or {}
	if isinstance(affected, str):
		affected = frappe.parse_json(affected) or {}
	if isinstance(affected, dict):
		affected = affected.get("output_types", [])
	if not affected:
		frappe.throw(_("No impacted outputs found for regeneration."), title=_("Addendum regeneration"))

	previous_current_by_type: dict[str, str] = {}
	for output_type in affected:
		row = frappe.db.get_value(
			"STD Generated Output",
			{"instance_code": impact.instance_code, "output_type": output_type, "status": "Current"},
			["output_code"],
			as_dict=True,
		)
		if row:
			previous_current_by_type[output_type] = row["output_code"]

	result = generate_std_outputs(
		instance_code=impact.instance_code,
		scope=affected,
		actor=actor,
		addendum_code=impact.addendum_code,
	)

	for out in result["outputs"]:
		ot = out["output_type"]
		frappe.db.set_value(
			"STD Generated Output",
			{"output_code": out["output_code"]},
			{
				"source_addendum_code": impact.addendum_code,
				"supersedes_output_code": previous_current_by_type.get(ot),
				"is_stale": 0,
				"stale_reason": None,
			},
			update_modified=False,
		)
		record_std_audit_event(
			"OUTPUT_REGENERATED",
			"STD Generated Output",
			out["output_code"],
			actor=actor,
			metadata={
				"impact_analysis_code": impact_analysis_code,
				"source_addendum_code": impact.addendum_code,
				"supersedes_output_code": previous_current_by_type.get(ot),
			},
		)

	transition_std_object("ADDENDUM_IMPACT", impact_analysis_code, "STD_ADDENDUM_MARK_REGENERATED", actor)

	return {
		"impact_analysis_code": impact_analysis_code,
		"status": "Regenerated",
		"generation_job_code": result["generation_job_code"],
		"outputs": result["outputs"],
	}
