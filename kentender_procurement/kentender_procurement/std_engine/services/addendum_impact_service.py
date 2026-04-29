from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.audit_service import record_std_audit_event
from kentender_procurement.std_engine.services.state_transition_service import transition_std_object

CHANGE_TYPE_TO_IMPACT = {
	"PARAMETER_VALUE_CHANGE": {"outputs": {"Bundle"}, "ack": True, "deadline_review": False},
	"BOQ_QUANTITY_CHANGE": {"outputs": {"Bundle", "DSM", "DEM", "DCM"}, "ack": True, "deadline_review": True},
	"BOQ_ITEM_ADD": {"outputs": {"Bundle", "DSM", "DEM", "DCM"}, "ack": True, "deadline_review": True},
	"BOQ_ITEM_DELETE": {"outputs": {"Bundle", "DSM", "DEM", "DCM"}, "ack": True, "deadline_review": True},
	"BOQ_ITEM_DESCRIPTION_CHANGE": {"outputs": {"Bundle", "DSM", "DEM", "DCM"}, "ack": True, "deadline_review": True},
	"WORKS_REQUIREMENT_CHANGE": {"outputs": {"Bundle", "DSM", "DEM", "DCM"}, "ack": True, "deadline_review": True},
	"SPECIFICATION_ATTACHMENT_CHANGE": {"outputs": {"Bundle", "DCM", "DEM"}, "ack": True, "deadline_review": True},
	"DRAWING_ATTACHMENT_CHANGE": {"outputs": {"Bundle", "DCM", "DEM"}, "ack": True, "deadline_review": True},
	"SUBMISSION_DEADLINE_CHANGE": {"outputs": {"Bundle", "DSM", "DOM"}, "ack": True, "deadline_review": True},
	"OPENING_DATETIME_CHANGE": {"outputs": {"Bundle", "DOM"}, "ack": True, "deadline_review": True},
	"TENDER_SECURITY_CHANGE": {"outputs": {"Bundle", "DSM", "DEM"}, "ack": True, "deadline_review": True},
	"EVALUATION_OPTION_CHANGE": {"outputs": {"Bundle", "DEM", "DSM", "DCM"}, "ack": True, "deadline_review": True},
	"SCC_VALUE_CHANGE": {"outputs": {"Bundle", "DCM"}, "ack": True, "deadline_review": False},
}


@frappe.whitelist()
def analyze_std_addendum_impact(
	instance_code: str, addendum_code: str, proposed_changes: list[dict[str, Any]], actor: str | None = None
) -> dict[str, Any]:
	"""STD-CURSOR-0801: analyze proposed change set and produce auditable impact map."""
	actor = actor or frappe.session.user
	if not frappe.db.exists("STD Instance", {"instance_code": instance_code}):
		frappe.throw(_("STD Instance not found."), title=_("Addendum impact"))
	if not proposed_changes:
		frappe.throw(_("At least one proposed change is required."), title=_("Addendum impact"))

	impact_code = f"IMPACT-{frappe.generate_hash(length=10).upper()}"
	doc = frappe.get_doc(
		{
			"doctype": "STD Addendum Impact Analysis",
			"impact_analysis_code": impact_code,
			"instance_code": instance_code,
			"addendum_code": addendum_code,
			"status": "Draft",
			"proposed_changes_json": json.dumps({"changes": proposed_changes}),
		}
	).insert(ignore_permissions=True)
	transition_std_object("ADDENDUM_IMPACT", impact_code, "STD_ADDENDUM_ANALYZE", actor)

	outputs: set[str] = set()
	requires_ack = False
	requires_deadline_review = False
	unknown: list[str] = []
	for change in proposed_changes:
		change_type = str(change.get("change_type") or "").strip().upper()
		meta = CHANGE_TYPE_TO_IMPACT.get(change_type)
		if not meta:
			unknown.append(change_type or "UNKNOWN")
			continue
		outputs.update(meta["outputs"])
		requires_ack = requires_ack or bool(meta["ack"])
		requires_deadline_review = requires_deadline_review or bool(meta["deadline_review"])

	transition_std_object("ADDENDUM_IMPACT", impact_code, "STD_ADDENDUM_COMPLETE_ANALYSIS", actor)
	frappe.db.set_value(
		"STD Addendum Impact Analysis",
		{"impact_analysis_code": impact_code},
		{
			"impacted_output_types_json": json.dumps({"output_types": sorted(outputs)}),
			"analysis_summary_json": json.dumps(
				{"proposed_change_count": len(proposed_changes), "unknown_change_types": unknown}
			),
			"requires_regeneration": 1 if outputs else 0,
			"requires_acknowledgement": 1 if requires_ack else 0,
			"requires_deadline_review": 1 if requires_deadline_review else 0,
		},
		update_modified=False,
	)
	if outputs:
		transition_std_object("ADDENDUM_IMPACT", impact_code, "STD_ADDENDUM_REQUIRE_REGEN", actor)
	else:
		transition_std_object("ADDENDUM_IMPACT", impact_code, "STD_ADDENDUM_APPROVE", actor)

	record_std_audit_event(
		"ADDENDUM_IMPACT_ANALYZED",
		"STD Addendum Impact Analysis",
		impact_code,
		actor=actor,
		metadata={"instance_code": instance_code, "impacted_output_types": sorted(outputs)},
	)
	doc.reload()
	return {
		"impact_analysis_code": impact_code,
		"status": doc.status,
		"impacted_output_types": sorted(outputs),
		"requires_acknowledgement": bool(doc.requires_acknowledgement),
		"requires_deadline_review": bool(doc.requires_deadline_review),
	}
