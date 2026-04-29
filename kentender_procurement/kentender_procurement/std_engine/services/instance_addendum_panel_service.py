"""STD workbench: addendum impact panel (STD-CURSOR-1107)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.std_engine.services.action_availability_service import (
	_perm_read,
	resolve_std_document,
)


def build_std_instance_addendum_impact_panel(instance_code: str, actor: str | None = None) -> dict[str, Any]:
	user = (actor or "").strip() or frappe.session.user
	if user in (None, "", "Guest"):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	code = (instance_code or "").strip()
	if not code:
		return {"ok": False, "error": "invalid", "message": str(_("Instance code is required."))}

	resolved = resolve_std_document("STD Instance", code)
	if not resolved:
		return {"ok": False, "error": "not_found", "message": str(_("No document matches this instance code."))}

	doctype, name, inst = resolved
	if doctype != "STD Instance" or not _perm_read(doctype, name, user):
		return {"ok": False, "error": "not_permitted", "message": str(_("Not permitted"))}

	rows = frappe.get_all(
		"STD Addendum Impact Analysis",
		filters={"instance_code": code},
		fields=[
			"impact_analysis_code",
			"addendum_code",
			"status",
			"requires_regeneration",
			"requires_acknowledgement",
			"requires_deadline_review",
			"impacted_output_types_json",
			"proposed_changes_json",
			"analysis_summary_json",
		],
		order_by="modified desc",
		limit=50,
	)

	supersession = frappe.get_all(
		"STD Instance",
		filters={"tender_code": inst.get("tender_code"), "instance_code": ("!=", code)},
		fields=["instance_code", "instance_status", "template_version_code"],
		limit=20,
	)

	return {
		"ok": True,
		"instance_code": code,
		"impact_analyses": rows,
		"regeneration_hints": {
			"boq": str(_("BOQ changes require Bundle / DSM / DEM / DCM regeneration when outputs are current.")),
			"deadline": str(_("Deadline changes require Bundle / DSM / DOM regeneration for opening-related outputs.")),
		},
		"supersession_chain": supersession,
	}
